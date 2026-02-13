import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any, Generator

from alibabacloud_aliding20230426.client import Client as AlidingClient
from alibabacloud_aliding20230426 import models as aliding_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from common.data_source.config import INDEX_BATCH_SIZE, DocumentSource
from common.data_source.exceptions import ConnectorMissingCredentialError
from common.data_source.interfaces import LoadConnector, PollConnector, SecondsSinceUnixEpoch
from common.data_source.models import Document, GenerateDocumentsOutput

ALIDING_SKILL_ID = "1270abf4-0a12-4696-9a53-311142e38996"


def _normalize_kb_urls(raw_urls: Any) -> list[str]:
    if raw_urls is None:
        return []
    if isinstance(raw_urls, list):
        return [str(url).strip() for url in raw_urls if str(url).strip()]
    if isinstance(raw_urls, str):
        parts = []
        for chunk in raw_urls.replace("\n", ",").split(","):
            chunk = chunk.strip()
            if chunk:
                parts.append(chunk)
        return parts
    return [str(raw_urls).strip()] if str(raw_urls).strip() else []


class AliDingKBConnector(LoadConnector, PollConnector):
    def __init__(
        self,
        public_account_id: str,
        kb_urls: list[str] | str,
        batch_size: int = INDEX_BATCH_SIZE,
        recall_as_file: bool = False,
        recall_library_with_docs: bool = True,
    ) -> None:
        self.public_account_id = public_account_id
        self.kb_urls = _normalize_kb_urls(kb_urls)
        self.batch_size = batch_size
        self.recall_as_file = recall_as_file
        self.recall_library_with_docs = recall_library_with_docs
        self._client: AlidingClient | None = None

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        access_key_id = credentials.get("access_key_id")
        access_key_secret = credentials.get("access_key_secret")
        if not access_key_id or not access_key_secret:
            raise ConnectorMissingCredentialError("AliDing KB credentials missing access_key_id/access_key_secret.")

        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        config.endpoint = "aliding.aliyuncs.com"
        self._client = AlidingClient(config)
        return None

    def _invoke_skill(self, url: str) -> list[dict[str, Any]]:
        if not self._client:
            raise ConnectorMissingCredentialError("AliDing KB credentials not loaded.")

        account_context = aliding_models.InvokeSkillHeadersAccountContext(
            account_id=self.public_account_id
        )
        invoke_skill_headers = aliding_models.InvokeSkillHeaders(
            account_context=account_context
        )

        params = {
            "urlList": [url],
            "recallAsFile": self.recall_as_file,
            "recallLibraryWithDocs": self.recall_library_with_docs,
        }

        request = aliding_models.InvokeSkillRequest(
            params=params,
            skill_id=ALIDING_SKILL_ID,
        )

        runtime = util_models.RuntimeOptions(
            read_timeout=30000,
            connect_timeout=10000,
        )

        response = self._client.invoke_skill_with_options(
            request,
            invoke_skill_headers,
            runtime,
        )
        return self._parse_response(response)

    def _fetch_kb_content(
        self,
        url_list: list[str],
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> list[dict[str, Any]]:
        all_results: list[dict[str, Any]] = []
        for url in url_list:
            attempt = 0
            while attempt < max_retries:
                try:
                    docs = self._invoke_skill(url)
                    logging.info(
                        "AliDing KB fetched %s document(s) from %s",
                        len(docs),
                        url,
                    )
                    all_results.extend(docs)
                    break
                except Exception as exc:
                    attempt += 1
                    error_msg = str(exc)
                    if "Read timed out" in error_msg and attempt < max_retries:
                        logging.warning(
                            "Fetch AliDing KB URL %s timed out, retrying (%s/%s)...",
                            url,
                            attempt,
                            max_retries,
                        )
                        time.sleep(retry_delay * attempt)
                        continue
                    logging.error(
                        "Failed to fetch AliDing KB content for %s after %s attempts: %s",
                        url,
                        attempt,
                        error_msg,
                    )
                    break
            time.sleep(1.0)
        logging.info("AliDing KB total fetched documents: %s", len(all_results))
        return all_results

    def _parse_response(self, response: Any) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        body = response.body.to_map()
        export_list = body.get("Data", {}).get("exportResultList", [])
        if not export_list:
            return results

        for item in export_list:
            if not item.get("success"):
                continue

            if item.get("doc"):
                doc = item["doc"]
                results.append(
                    {
                        "title": doc.get("title", "Untitled"),
                        "content": doc.get("data", ""),
                        "url": doc.get("link", item.get("url", "")),
                        "doc_id": doc.get("notifyKey"),
                    }
                )
            elif item.get("library"):
                library = item["library"]
                directory = library.get("directory", [])

                def extract_docs(dirs: list[dict[str, Any]], parent_path: str = "") -> None:
                    for dir_item in dirs:
                        dir_title = dir_item.get("title", "")
                        current_path = f"{parent_path}/{dir_title}" if parent_path else dir_title
                        children = dir_item.get("children", [])

                        for child in children:
                            if child.get("doc"):
                                doc = child["doc"]
                                doc_title = doc.get("title", "Untitled")
                                display_title = f"{current_path}/{doc_title}" if current_path else doc_title
                                results.append(
                                    {
                                        "title": display_title,
                                        "content": doc.get("data", ""),
                                        "url": doc.get("link", child.get("link", "")),
                                        "doc_id": doc.get("notifyKey"),
                                    }
                                )
                            if child.get("children"):
                                extract_docs([child], current_path)

                extract_docs(directory)

        return results

    def _build_document(self, doc: dict[str, Any]) -> Document:
        title = doc.get("title") or "Untitled"
        content = doc.get("content") or ""
        url = doc.get("url") or ""
        doc_id = doc.get("doc_id") or url or title
        doc_hash = hashlib.sha256(str(doc_id).encode("utf-8")).hexdigest()

        blob = content.encode("utf-8")
        now = datetime.now(timezone.utc)

        return Document(
            id=f"aliding_kb:{doc_hash}",
            source=DocumentSource.ALIDING_KB,
            semantic_identifier=title,
            extension=".md",
            blob=blob,
            doc_updated_at=now,
            size_bytes=len(blob),
            metadata={
                "url": url,
                "aliding_doc_id": doc.get("doc_id"),
            },
        )

    def load_from_state(self) -> GenerateDocumentsOutput:
        if not self._client:
            raise ConnectorMissingCredentialError("AliDing KB credentials not loaded.")
        if not self.public_account_id:
            raise ValueError("AliDing KB public_account_id is required.")
        if not self.kb_urls:
            raise ValueError("AliDing KB kb_urls is required.")

        batch: list[Document] = []
        docs = self._fetch_kb_content(self.kb_urls)
        for doc in docs:
            batch.append(self._build_document(doc))
            if len(batch) >= self.batch_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def poll_source(
        self,
        start: SecondsSinceUnixEpoch,
        end: SecondsSinceUnixEpoch,
    ) -> Generator[list[Document], None, None]:
        for batch in self.load_from_state():
            if batch:
                yield batch

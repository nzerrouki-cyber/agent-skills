# services/discovery_engine.py
from google.cloud import discoveryengine_v1 as discoveryengine
from services.base_service import BaseService


class DiscoveryEngineService(BaseService):
    """Executes asynchronous RAG searches against Vertex AI Search Data Stores."""

    def __init__(self):
        super().__init__()
        self.client = discoveryengine.SearchAsyncClient()

    # Search for Vertex AI Data Store based on the datastore_id (category)
    async def search_datastore(
        self,
        datastore_id: str,
        query_text: str,
        top_k: int = 3
    ) -> str:
        """Queries Vertex AI Search Data Stores enforcing top_k boundary caps."""
        serving_config = self.client.serving_config_path(
            project=self.project_id,
            location=self.region,  # Binds dynamically to settings.REGION (us-central1)
            data_store=datastore_id,
            serving_config="default_search"
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query_text,
            page_size=top_k
        )

        try:
            response = await self.client.search(request=request)
            snippets = []
            # Retrieve knowledge files from the correct Vertex AI Data Store
            async for row in response:
                document_data = row.document.derived_struct_data
                data_dict = dict(document_data) if document_data else {}
                row_snippets = data_dict.get("snippets", [])
                
                if row_snippets and isinstance(row_snippets, list):
                    first_snippet = row_snippets[0]
                    if isinstance(first_snippet, dict):
                        snippets.append(first_snippet.get("snippet", ""))

            return "\n\n".join(snippets) if snippets else "No relevant context retrieved from Data Store."
        except Exception as e:
            return f"[Vertex AI Search Warning: Unable to query Datastore '{datastore_id}': {str(e)}]"
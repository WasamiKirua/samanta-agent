import logging
import traceback
from typing import List, Optional
from datetime import datetime, timezone
from contextlib import contextmanager

import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances
from weaviate.classes.query import MetadataQuery

from ai_companion.modules.memory.long_term.base_vector_store import BaseVectorStore, Memory
from ai_companion.settings import settings


# Configure root logger to ensure logs are visible
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weaviate_store")
logger.setLevel(logging.DEBUG)


class WeaviateStore(BaseVectorStore):
    """A class to handle vector storage operations using Weaviate."""

    REQUIRED_ENV_VARS = ["WEAVIATE_HOST", "WEAVIATE_PORT"]
    DISTANCE_THRESHOLD = 0.3  # Maximum distance for considering memories as similar (lower = more similar)
    # IMPORTANT: Using uppercase first letter as that's what Weaviate seems to expect
    COLLECTION_NAME = "Long_term_memory"

    _instance: Optional["WeaviateStore"] = None
    _initialized: bool = False

    def __new__(cls) -> "WeaviateStore":
        logger.info("WeaviateStore.__new__ called")
        if cls._instance is None:
            logger.info("Creating new WeaviateStore instance")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        logger.info("WeaviateStore.__init__ called, initialized=%s", self._initialized)
        if not self._initialized:
            # Setup logging
            self.logger = logger
            
            # Validate environment variables
            self._validate_env_vars()

            # Connect to Weaviate
            try:
                self.logger.info(f"Connecting to Weaviate at {settings.WEAVIATE_HOST}:{settings.WEAVIATE_PORT}")
                
                # Connect to Weaviate using the correct method
                self.client = weaviate.connect_to_custom(
                    http_host=settings.WEAVIATE_HOST,
                    http_port=settings.WEAVIATE_PORT,
                    http_secure=False,
                    grpc_host=settings.WEAVIATE_HOST,
                    grpc_port=50051,
                    grpc_secure=False,
                )
                
                # Connect to Weaviate
                self.client.connect()
                self.logger.info("Successfully connected to Weaviate")
                
                # Just log existing collections for debugging
                try:
                    # Using collections.list_all()
                    collections = self.client.collections.list_all()
                    self.logger.info(f"Existing collections: {collections}")
                except Exception as e:
                    self.logger.error(f"Error listing collections: {str(e)}")
                
                self._initialized = True
                self.logger.info("WeaviateStore fully initialized")
            except Exception as e:
                self.logger.error(f"Error initializing WeaviateStore: {str(e)}")
                self.logger.error(traceback.format_exc())
                raise

    def __del__(self):
        """Cleanup when the instance is destroyed."""
        if hasattr(self, 'client'):
            self.logger.info("Closing Weaviate connection")
            try:
                self.client.close()
            except Exception as e:
                self.logger.error(f"Error closing Weaviate connection: {str(e)}")

    def close(self):
        """Explicitly close the Weaviate connection."""
        if hasattr(self, 'client'):
            self.logger.info("Closing Weaviate connection")
            try:
                self.client.close()
            except Exception as e:
                self.logger.error(f"Error closing Weaviate connection: {str(e)}")

    @contextmanager
    def get_client(self):
        """Context manager for getting a fresh connection to Weaviate."""
        client = None
        try:
            # Create a new connection
            client = weaviate.connect_to_custom(
                http_host=settings.WEAVIATE_HOST,
                http_port=settings.WEAVIATE_PORT,
                http_secure=False,
                grpc_host=settings.WEAVIATE_HOST,
                grpc_port=50051,
                grpc_secure=False,
            )
            client.connect()
            yield client
        except Exception as e:
            self.logger.error(f"Error in get_client: {str(e)}")
            raise
        finally:
            if client:
                try:
                    client.close()
                except Exception as e:
                    self.logger.error(f"Error closing client in context manager: {str(e)}")

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = []
        for var in self.REQUIRED_ENV_VARS:
            value = getattr(settings, var, None)
            if value is None:
                missing_vars.append(var)
                self.logger.error(f"Missing required environment variable: {var}")
            else:
                self.logger.info(f"Environment variable {var} is set to: {value}")
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def _collection_exists(self) -> bool:
        """Check if the memory collection exists."""
        try:
            # Get all collections and check if our collection exists
            collections = self.client.collections.list_all()
            collection_names = [collection for collection in collections]
            self.logger.info(f"Available collections: {collection_names}")
            exists = self.COLLECTION_NAME in collection_names
            self.logger.info(f"Collection {self.COLLECTION_NAME} exists: {exists}")
            return exists
        except Exception as e:
            self.logger.error(f"Error checking if collection exists: {str(e)}")
            return False

    def _create_collection(self) -> None:
        """Create a new collection for storing memories if it doesn't exist."""
        if self._collection_exists():
            self.logger.info(f"Collection {self.COLLECTION_NAME} already exists")
            return
            
        try:
            # Create the collection with the exact configuration from the notebook
            self.logger.info(f"Creating collection {self.COLLECTION_NAME}")
            self.client.collections.create(
                self.COLLECTION_NAME,
                vectorizer_config=[
                    Configure.NamedVectors.text2vec_transformers(
                        name="text_vector",
                        source_properties=["text"],
                        vector_index_config=Configure.VectorIndex.hnsw(
                            distance_metric=VectorDistances.COSINE
                        )
                    )
                ],
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="timestamp", data_type=DataType.DATE),
                    Property(name="uuid", data_type=DataType.UUID)
                ]
            )
            
            # Verify the collection was created
            if self._collection_exists():
                self.logger.info(f"Successfully created collection {self.COLLECTION_NAME}")
            else:
                self.logger.error(f"Failed to verify collection was created")
                
        except Exception as e:
            self.logger.error(f"Error creating collection: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def find_similar_memory(self, text: str) -> Optional[Memory]:
        """Find if a similar memory already exists."""
        try:
            if not self._collection_exists():
                self.logger.info("Collection does not exist, returning None")
                return None
                
            self.logger.info(f"Finding similar memory for text: {text[:50]}...")
            collection = self.client.collections.get(self.COLLECTION_NAME)
            response = collection.query.near_text(
                query=text,
                limit=1,
                distance=self.DISTANCE_THRESHOLD,  # Maximum distance threshold
                return_metadata=MetadataQuery(distance=True)
            )

            if response.objects:
                obj = response.objects[0]
                # Convert distance to similarity score (1 - distance)
                similarity_score = 1 - obj.metadata.distance
                self.logger.info(f"Found similar memory with score: {similarity_score}")
                return Memory(
                    text=obj.properties["text"],
                    metadata={k: v for k, v in obj.properties.items() if k != "text"},
                    score=similarity_score
                )
            self.logger.info("No similar memory found")
            return None
        except Exception as e:
            self.logger.error(f"Error in find_similar_memory: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def store_memory(self, text: str, metadata: dict) -> None:
        """Store a new memory in the vector store."""
        try:
            # Create collection if it doesn't exist
            if not self._collection_exists():
                self._create_collection()
                
            self.logger.info(f"Storing memory: {text[:50]}...")
            collection = self.client.collections.get(self.COLLECTION_NAME)
            
            # Check if similar memory exists
            similar_memory = self.find_similar_memory(text)
            if similar_memory and similar_memory.id:
                self.logger.info(f"Updating existing memory with ID: {similar_memory.id}")
                # For updates we'll use the existing UUID
                uuid_value = similar_memory.id
            else:
                # For new entries, get UUID from metadata if available
                uuid_value = metadata.get("uuid") or metadata.get("id")
            
            # Create properties dictionary WITHOUT id/uuid
            properties = {
                "text": text,
            }
            
            # Format timestamp for Weaviate (RFC3339 with timezone)
            if "timestamp" in metadata:
                # If timestamp is a string, try to parse it
                if isinstance(metadata["timestamp"], str):
                    try:
                        # Try to parse the timestamp string
                        dt = datetime.fromisoformat(metadata["timestamp"].replace('Z', '+00:00'))
                        # Convert to local timezone and format as RFC3339
                        local_time = dt.astimezone()
                        properties["timestamp"] = local_time.isoformat()
                    except ValueError:
                        # If parsing fails, use current time
                        local_time = datetime.now(timezone.utc).astimezone()
                        properties["timestamp"] = local_time.isoformat()
                else:
                    # If timestamp is already a datetime object, use it directly
                    dt = metadata["timestamp"]
                    if dt.tzinfo is None:
                        # If no timezone info, assume UTC
                        dt = dt.replace(tzinfo=timezone.utc)
                    local_time = dt.astimezone()
                    properties["timestamp"] = local_time.isoformat()
            else:
                # If no timestamp provided, use current time
                local_time = datetime.now(timezone.utc).astimezone()
                properties["timestamp"] = local_time.isoformat()
            
            # Add any other metadata EXCEPT id/uuid
            for key, value in metadata.items():
                if key not in ["id", "uuid", "timestamp"]:  # Skip id, uuid, and timestamp as we've handled them
                    properties[key] = value

            self.logger.info(f"Storing with properties: {properties}")
            
            # Use batch approach instead of direct insert
            with collection.batch.dynamic() as batch:
                if uuid_value:
                    # If we have a UUID, use it explicitly
                    batch.add_object(
                        properties=properties,
                        uuid=uuid_value
                    )
                else:
                    # Let Weaviate generate a UUID
                    batch.add_object(
                        properties=properties
                    )
                
                # Check for errors
                if batch.number_errors > 0:
                    failed_objects = collection.batch.failed_objects
                    if failed_objects:
                        self.logger.error(f"Failed to store memory: {failed_objects[0]}")
                        raise Exception(f"Failed to store memory: {failed_objects[0]}")
            
            self.logger.info("Memory stored successfully")
        except Exception as e:
            self.logger.error(f"Error in store_memory: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def search_memories(self, query: str, k: int = 5) -> List[Memory]:
        """Search for similar memories in the vector store."""
        try:
            if not self._collection_exists():
                self.logger.info("Collection does not exist, returning empty list")
                return []
                
            self.logger.info(f"Searching memories for query: {query[:50]}... (k={k})")
            collection = self.client.collections.get(self.COLLECTION_NAME)
            response = collection.query.near_text(
                query=query,
                limit=k,
                return_metadata=MetadataQuery(distance=True)
            )

            results = [
                Memory(
                    text=obj.properties["text"],
                    metadata={k: v for k, v in obj.properties.items() if k != "text"},
                    score=1 - obj.metadata.distance  # Convert distance to similarity score
                )
                for obj in response.objects
            ]
            
            self.logger.info(f"Found {len(results)} memories")
            return results
        except Exception as e:
            self.logger.error(f"Error in search_memories: {str(e)}")
            self.logger.error(traceback.format_exc())
            return [] 
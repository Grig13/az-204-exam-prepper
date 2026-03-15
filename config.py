import os

# --- FILE CONFIGURATION ---
PDF_INPUT_FILE = "AZ-204.pdf"  # Change this for other exams
OUTPUT_JSON_FILE = "Exam_Final_Engine.json"

# --- DIRECTORIES ---
IMAGES_DIR = "images"         # Cropped diagrams from questions
SNAPSHOTS_DIR = "pdf_pages"   # Full page snapshots for validation

# --- AUTO-TAGGING KEYWORDS (Extensible) ---
# Add more topics here as needed for other exams
TOPIC_KEYWORDS = {
    "Azure Functions": ["azure function", "function app", "durable function", "trigger", "binding", "custom handler"],
    "Cosmos DB": ["cosmos db", "consistency level", "partition key", "sql api", "gremlin", "mongo", "change feed"],
    "App Service": ["app service", "web app", "app service plan", "scale up", "scale out", "autoscale", "deployment slot"],
    "Storage": ["blob storage", "storage account", "access tier", "lifecycle management", "blob lease", "table storage"],
    "Security & Identity": ["key vault", "managed identity", "active directory", "entra id", "sas token", "authentication", "authorization", "service principal"],
    "Containers": ["docker", "kubernetes", "aks", "container registry", "acr", "container instance", "helm"],
    "Messaging": ["event grid", "event hub", "service bus", "queue", "topic", "notification hub"],
    "Monitoring": ["application insights", "azure monitor", "log analytics", "telemetry", "alerts"],
    "Caching": ["redis", "cache", "cdn", "front door", "traffic manager"],
    "Logic Apps": ["logic app", "workflow", "connector"]
}

import psycopg2
import requests
from PIL import Image
from io import BytesIO
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split

# ------------------------------------------
# Configs
DB_CONFIG = {
    "dbname": "mlops_data",
    "user": "airflow",
    "password": "airflow",
    "host": "postgres",
    "port": "5432"
}

IMG_SIZE = (224, 224)
BATCH_SIZE = 32

# ------------------------------------------
# Transform for preprocessing
transform = transforms.Compose([
    transforms.Resize(IMG_SIZE),
    transforms.ToTensor(),
])

# ------------------------------------------
# Dataset Class
class PlantDataset(Dataset):
    def __init__(self, data, transform=None):
        self.data = data  # list of (url, label)
        self.transform = transform
        self.label_map = {"dandelion": 0, "grass": 1}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        url, label = self.data[idx]
        try:
            response = requests.get(url, timeout=10)
            image = Image.open(BytesIO(response.content)).convert("RGB")
        except Exception as e:
            print(f"Failed to load image from {url}: {e}")
            image = Image.new("RGB", IMG_SIZE)  # dummy black image

        if self.transform:
            image = self.transform(image)

        return image, self.label_map[label]

# ------------------------------------------
# Fetch Data from PostgreSQL
def fetch_image_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT url_source, label FROM plants_data WHERE url_source IS NOT NULL;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data  # list of (url, label)

# ------------------------------------------
# Create DataLoaders
def get_dataloaders(test_size=0.2, batch_size=BATCH_SIZE):
    all_data = fetch_image_data()
    train_data, val_data = train_test_split(
        all_data, test_size=test_size, stratify=[label for _, label in all_data]
    )

    train_dataset = PlantDataset(train_data, transform=transform)
    val_dataset = PlantDataset(val_data, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader

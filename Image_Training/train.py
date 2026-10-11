import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.nn import MSELoss
from dataset import PropertyDataset
from model import PropertyScorer
from transforms import train_tfms, val_tfms
from sklearn.metrics import mean_absolute_error, r2_score

def train_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = PropertyScorer().to(device)

    train_ds = PropertyDataset('Image_Training/data/train', transform=train_tfms)
    val_ds   = PropertyDataset('Image_Training/data/val', transform=val_tfms)
    train_dl = DataLoader(train_ds, batch_size=16, shuffle=True, num_workers=4)
    val_dl   = DataLoader(val_ds, batch_size=16)

    optimizer = AdamW(model.parameters(), lr=1e-4)
    criterion = MSELoss()

    for epoch in range(20):
        model.train()
        train_loss = 0

        for street, map, y in train_dl:
            street, map, y = street.to(device).float(), map.to(device).float(), y.to(device).float()

            preds = model(street, map)
            loss = criterion(preds, y)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for street, map, y in val_dl:
                street, map, y = street.to(device).float(), map.to(device).float(), y.to(device).float()
                preds = model(street, map)
                val_loss += criterion(preds, y).item()

        print(f"Epoch {epoch+1}: "
              f"Train MSE={train_loss/len(train_dl):.3f}, "
              f"Val MSE={val_loss/len(val_dl):.3f}")

    torch.save(model.state_dict(), "property_scorer.pt")


def test_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    y_true, y_pred = [], []

    val_ds   = PropertyDataset('Image_Training/data/val', transform=val_tfms)
    val_dl   = DataLoader(val_ds, batch_size=16)

    model = PropertyScorer().to(device)
    model.load_state_dict(torch.load("property_scorer1.pt"))
    model.eval()
    with torch.no_grad():
        for street, map, y in val_dl:
            preds = model(street.to(device), map.to(device))
            y_true.extend(y.numpy())
            y_pred.extend(preds.cpu().numpy())

    print("MAE:", mean_absolute_error(y_true, y_pred))
    print("R² :", r2_score(y_true, y_pred))


if __name__ == '__main__':
    train_model()
    # test_model()
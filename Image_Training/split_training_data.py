import pandas as pd
import os
import shutil
from sklearn.model_selection import train_test_split


def set_cwd():
    """
    Sets the current working directory to the script's location.
    """
    cwd = os.getcwd().split('\\')[-1]
    if cwd != 'Image_Training':
        os.chdir('Image_Training')
    return


def split_training_data():
    """
    Splits the full dataset into training and validation sets,
    ensuring that the distribution of ratings is preserved in both sets.
    """

    # Set working directory to script location
    set_cwd()

    # Read in the full dataset
    df = pd.read_csv('props_screened.csv')

    # Drop rows that don't have a rating
    df.dropna(subset=['rating'], inplace=True)

    # Create bins - in case any ratings are non-integer
    df['rating_bin'] = pd.cut(
        df['rating'],
        bins=[-0.1, 1, 2, 3, 4, 5.1],
        labels=[0, 1, 2, 3, 4]
    )

    train_df, val_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df['rating_bin']
    )

    # Drop helper column
    train_df = train_df.drop(columns=['rating_bin'])
    val_df   = val_df.drop(columns=['rating_bin'])

    train_df.to_csv('data/train/labels.csv', index=False)
    val_df.to_csv('data/val/labels.csv', index=False)

    return


def plot_data_distribution():
    """
    Plot the distribution of ratings in the training and validation sets
    to ensure they are similar.
    """

    import matplotlib.pyplot as plt

    # Set working directory to script location
    set_cwd()

    train_df = pd.read_csv('data/train/labels.csv')
    val_df   = pd.read_csv('data/val/labels.csv')

    plt.hist(train_df["rating"], bins=20, alpha=0.5, label="train")
    plt.hist(val_df["rating"], bins=20, alpha=0.5, label="val")
    plt.legend()

    plt.show()

    return


def create_image_folders():
    """
    Create folders for each view in train and val directories   
    Will delete any images that are not in the labels.csv files
    """

    # Set working directory to script location
    set_cwd()

    views = ['CountyView', 'StreetView', 'MapView', 'MapWideView']
    ext = {'CountyView': 'png',
           'StreetView': 'jpg',
           'MapView': 'jpg',
           'MapWideView': 'jpg'}

    for dir in ['train', 'val']:
        # Read in the dataset
        df = pd.read_csv('data/' + dir + '/labels.csv')

        # Create necessary directories if they don't exist
        for view in views:
            os.makedirs('data/' + dir + '/' + view, exist_ok=True)

            # Check if existing files need to be removed
            existing_files = os.listdir('data/' + dir + '/' + view)
            if len(existing_files) > 0:
                for file in existing_files:
                    if file.split('.')[0] not in df['taxmap'].astype(str).values:
                        os.remove(os.path.join('data/' + dir + '/' + view, file))
                    
        # Copy images to the appropriate folders
        for _, row in df.iterrows():
            for view in views:
                src = os.path.join('../Counties/Greenville', view, f"{row['taxmap']}.{ext[view]}")
                dst = os.path.join('data', dir, view, f"{row['taxmap']}.{ext[view]}")
                if os.path.exists(src):
                    if not os.path.exists(dst):
                        shutil.copy(src, dst)

    return


if __name__ == '__main__':
    # split_training_data()
    # plot_data_distribution()
    create_image_folders()
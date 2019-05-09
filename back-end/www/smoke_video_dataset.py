import torch
from torch.utils.data import Dataset
import cv2 as cv
import numpy as np
from optical_flow import OpticalFlow
from util import *

# The smoke video dataset
class SmokeVideoDataset(Dataset):
    def __init__(self, metadata_path=None, root_dir=None, mode="rgb", transform=None):
        """
        metadata_path (string): the full path to the video metadata json file
        root_dir (string): the root directory that stores video files
        transform (callable, optional): optional transform to be applied on a video
        """
        self.metadata = load_json(metadata_path)
        self.root_dir = root_dir
        self.mode = mode # can be "rgb" or "flow"
        self.transform = transform

    def __len__(self):
        return len(self.metadata)

    def __getitem__(self, idx):
        v = self.metadata[idx]
        file_path = os.path.join(self.root_dir, v["file_name"] + ".mp4")
        
        # Load rgb or optical flow as a data point
        if self.mode == "rgb":
            frames = load_rgb_frames(file_path)
        elif self.mode == "flow":
            return None
        else:
            return None

        # Transform the data point (e.g., data augmentation)
        if self.transform:
            frames = self.transform(frames)
        
        # Determine the label of the data point
        label_state = v["label_state_admin"] # TODO: need to change this to label_state in the future
        pos = [47, 23, 19, 15]
        neg = [32, 20, 16, 12]
        label = None
        if label_state in pos:
            label = 1
        elif label_state in neg:
            label = 0

        # Return item
        return {"frames": frames_to_tensor(frames), "label": label, "file_name": v["file_name"]}

# Load videos in the RGB format
def load_rgb_frames(file_path, resize_to=224.0):
    op = OpticalFlow()
    
    # The vid_to_imgs function gives (time, height, width, channel)
    frames = op.vid_to_imgs(rgb_vid_path=file_path)
    t, h, w, c = frames.shape
    
    # Resize and scale images for the network structure
    frames_out = []
    need_resize = False
    if w < resize_to or h < resize_to:
        d = resize_to - min(w, h)
        sc = 1 + d / min(w, h)
        need_resize = True
    for i in range(t):
        img = frames[i, :, :, :]
        if need_resize:
            img = cv.resize(img, dsize=(0, 0), fx=sc, fy=sc)
        img = (img / 255.) * 2 - 1
        frames_out.append(img)
    return np.asarray(frames_out, dtype=np.float32)


def frames_to_tensor(frames):
    """
    Converts a numpy.ndarray with shape (time x height x width x channel)
    to a torch.FloatTensor of shape (channel x time x height x width)
    """
    return torch.from_numpy(frames.transpose([3,0,1,2]))

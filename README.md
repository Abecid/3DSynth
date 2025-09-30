# Generate Synthetic 3D Samples for Training / Eval

## Environment Setup
```
conda create -n syn python-3.10
conda activate syn
pip install -r requirements.txt
```

## Create dataset
glb_directory contains subfolders containing a mesh (.glb) and size.json (with min and max values)
```
python generate_dataset.py -glb_dir {glb_directory}
```
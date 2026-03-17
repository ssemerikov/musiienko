# GPU Translation with Google Colab + VS Code Integration

## Quick Start

### Option 1: Google Drive (Recommended)

1. **Upload data to Google Drive:**
   ```bash
   # Run this to create the upload package
   python3 prepare_colab_upload.py
   ```
   This creates `colab_upload/thesis_data.zip` - upload this to your Google Drive.

2. **Open Colab notebook:**
   - Go to [Google Colab](https://colab.research.google.com)
   - Upload `notebooks/translate_ukrainian_to_english.ipynb`
   - Or open from GitHub if you push the repo

3. **Run the notebook:**
   - Select Runtime → Change runtime type → GPU (T4)
   - Run all cells
   - Translation takes ~30-60 minutes for 4,027 files

### Option 2: VS Code + Colab Integration

#### Method A: Jupyter Extension (Easiest)

1. Install VS Code extensions:
   - "Jupyter" (Microsoft)
   - "Python" (Microsoft)

2. Open the `.ipynb` file in VS Code

3. Select kernel: Click "Select Kernel" → "Existing Jupyter Server"

4. Enter Colab URL:
   - In Colab, run: `from google.colab import output; output.serve_kernel_port_as_window(9000)`
   - Copy the URL and paste in VS Code

#### Method B: SSH Tunnel (Full IDE Access)

1. In Colab, run:
   ```python
   !pip install colab-ssh
   from colab_ssh import launch_ssh_cloudflared
   launch_ssh_cloudflared(password="your_password")
   ```

2. Install cloudflared on your machine:
   ```bash
   # Linux
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
   chmod +x cloudflared-linux-amd64
   sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
   ```

3. In VS Code:
   - Install "Remote - SSH" extension
   - Add SSH host with the cloudflared URL from Colab
   - Connect and open `/content` folder

### Option 3: Direct ZIP Upload

1. Create ZIP of text files:
   ```bash
   cd data
   zip -r text_by_level.zip text_by_level/
   ```

2. In Colab:
   - Set `USE_LOCAL_UPLOAD = True` in config cell
   - Upload `text_by_level.zip` when prompted
   - Download `text_english.zip` when complete

## Expected Performance

| GPU Type | Files/min | Total Time (4,027 files) |
|----------|-----------|--------------------------|
| T4       | ~70       | ~60 min                  |
| V100     | ~120      | ~35 min                  |
| A100     | ~200      | ~20 min                  |
| CPU only | ~0.5      | ~130 hours               |

## File Structure

```
colab_upload/
├── thesis_data.zip          # Data package for Google Drive
│   ├── text_by_level/       # Ukrainian source texts (4,027 files)
│   └── raw/                 # JSON metadata (132 files)
└── notebooks/
    └── translate_ukrainian_to_english.ipynb
```

## After Translation

1. Download `text_english/` from Google Drive
2. Copy to `data/text_english/` in your project
3. Run analysis with English texts:
   ```bash
   python3 run_english_analysis.py
   ```

## Troubleshooting

### "CUDA out of memory"
- Reduce `batch_size` in `translate_batch()` from 16 to 8 or 4
- Add `torch.cuda.empty_cache()` more frequently

### "Rate limit exceeded"
- Colab has usage limits; wait or use Colab Pro

### "Model loading fails"
- Check internet connection
- Try restarting runtime

### VS Code can't connect
- Ensure cloudflared is installed correctly
- Check that Colab runtime is still active (12-hour limit)

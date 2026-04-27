# BioVL-QR Video Annotator

A static web app for annotating biology experiment videos. Hosted on GitHub Pages — no server required.

## How it works

1. Annotators open the shared link
2. They enter their first and last name
3. They watch 30-second video segments and type descriptions
4. Annotations are auto-saved in the browser (localStorage)
5. When finished, they click **Export JSON** and send you the file

## Deploy to GitHub Pages

1. Create a new GitHub repository (e.g. `biovl-annotator`)

2. Push this folder to the repo:
   ```bash
   cd video_annotator_web
   git init
   git add .
   git commit -m "Initial annotator deploy"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/biovl-annotator.git
   git push -u origin main
   ```

3. Enable GitHub Pages:
   - Go to **Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: **main**, folder: **/ (root)**
   - Click **Save**

4. After a minute, your site will be live at:
   ```
   https://YOUR_USERNAME.github.io/biovl-annotator/
   ```

5. Share that link with your annotators.

## Adding more videos

1. Place the `.mp4` file in the `videos/` folder (must be H.264 encoded)
2. Edit the `VIDEOS` array at the top of the `<script>` in `index.html`:
   ```js
   const VIDEOS = [
     { id: 'electrophoresis_1', label: 'Electrophoresis 1', src: 'videos/electrophoresis_1.mp4' },
     { id: 'extractdna_1',      label: 'Extract DNA 1',     src: 'videos/extractdna_1.mp4' },
     { id: 'new_video',         label: 'New Video',         src: 'videos/new_video.mp4' },
   ];
   ```
3. Commit and push — GitHub Pages will update automatically.

## Notes

- Videos must be H.264/MP4 for browser playback. Use ffmpeg to convert:
  ```bash
  ffmpeg -i input.mp4 -vf scale=1280:720 -r 15 -c:v libx264 -crf 28 -pix_fmt yuv420p -movflags +faststart -an output.mp4
  ```
- GitHub has a 100 MB per-file limit. Keep videos under that.
- Each annotator's work is stored independently in their browser's localStorage, keyed by their name.
- The exported JSON includes the annotator's name, video ID, timestamps, and all segment descriptions.

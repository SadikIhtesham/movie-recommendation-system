# Movie Recommender System

A Streamlit movie recommender using the movie catalogue and tags stored in
`movie_dict.pkl`. The app calculates cosine similarity when a user selects a
movie. It does **not** require `similarity.pkl`, Google Drive, or `gdown`.

## Included files

- `app.py` — Streamlit application
- `movie_dict.pkl` — movie catalogue and tags
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — application theme
- `.streamlit/secrets.toml.example` — example secret configuration
- `assets/poster-placeholder.svg` — fallback image when a poster is unavailable

## Deploy on Streamlit Community Cloud

1. Upload all files and folders from this project to the root of your GitHub
   repository.
2. Open <https://share.streamlit.io/> and sign in with GitHub.
3. Select **Create app** and enter:
   - Repository: `SadikIhtesham/codes2`
   - Branch: `main`
   - Main file path: `app.py`
4. Open **Advanced settings** and add the following under **Secrets**:

   ```toml
   TMDB_API_KEY = "your_new_tmdb_api_key"
   ```

5. Select Python 3.12 and click **Deploy**.

The recommendation system works without a TMDB key, but poster images will use
the included placeholder. A TMDB key is required to display real posters.

## Important security step

The old TMDB API key appeared in the previous public `app.py`. Revoke that key
in your TMDB account and generate a new one. Add the new key only through
Streamlit Secrets; do not paste it into `app.py` or commit it to GitHub.

## Run locally

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
streamlit run app.py
```

macOS or Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

Before running, edit `.streamlit/secrets.toml` and insert your new TMDB API
key. The file is ignored by Git and should remain private.


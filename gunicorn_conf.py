# gunicorn_conf.py
import multiprocessing
import os

# Adresse et port — PORT vient de l'environnement si l'hébergeur en impose
# un (Render, Railway...), avec 8000 comme repli en local/VPS.
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Formule standard : (2 x nombre de coeurs CPU) + 1.
# À revoir à la baisse si le VPS choisi a peu de RAM — chaque worker sync
# charge une copie complète de l'app.
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"

timeout = 30
keepalive = 2

# Logs vers stdout/stderr — un vrai hébergeur (VPS, Render...) les capture ;
# à rediriger vers un fichier seulement si l'hébergeur ne le fait pas déjà.
accesslog = "-"
errorlog = "-"
loglevel = "info"

proc_name = "coja7_gunicorn"

# reload = True  # utile en dev/staging uniquement, jamais en prod

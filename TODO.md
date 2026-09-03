
3. Les pdf 
4. Le stockage (Blackblase ppur audios et ImageKot pour images)
5. Les search bars (Médias, Rubriques, Sermons)
7. Le petit bleu au clic
8. Téléchargement des médias et gallerie
9. Ajouter les trucs de SEO (author...)
10. Lier la page about
11. Apprendre le MarkDown
12. Le Téléchargement des médias restent encore à être résolu
13. Les outils SEO
14. 

Admin
1. Clique pour fermer la navbar


  <!--
  <div class="thumb {{ 'video' if item.type == 'sermon' }} tone-{{ item.tone }}"></div>
  -->
  
  Index.html
  {% if federation %}
<a class="federation" style="text-decoration:none;color:inherit;"
   href="{{ url_for('communications.federation_detail', note_id=federation.data.id, federation=federation.data.department) }}">
  <img class="seal-watermark" src="{{ url_for('static', filename='img/logo.jpg') }}" alt="Logo COJA7">
  <div class="ref">{{ federation.data.federation | upper or "" }} · {{ federation.data.reference_number or "Note" }}</div>
  <h3>{{ federation.data.title }}</h3>
  <div class="meta">Publié le {{ federation.data.published_at | date_fr }} · {{ federation.data.department or "" }}</div>
</a>
{% endif %}
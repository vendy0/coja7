  (function () {
    "use strict";

    var root = document.getElementById("calendar-root");
    var CALENDAR_URL = root.dataset.calendarUrl;
    var EVENTS_URL = root.dataset.eventsUrl;
    var EVENT_URL_TEMPLATE = root.dataset.eventUrlTemplate;

    function eventUrl(id) {
      return EVENT_URL_TEMPLATE.replace("__EVENT_ID__", encodeURIComponent(id));
    }

    var monthLabelEl = document.getElementById("month-label");
    var daysEl = document.getElementById("calendar-days");
    var eventsHeadingEl = document.getElementById("events-heading");
    var eventsListEl = document.getElementById("events-list");

    var navPrevYear = document.getElementById("nav-prev-year");
    var navPrevMonth = document.getElementById("nav-prev-month");
    var navNextMonth = document.getElementById("nav-next-month");
    var navNextYear = document.getElementById("nav-next-year");

    function escapeHtml(str) {
      if (!str) return "";
      return String(str).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
      });
    }

    function statusTag(status) {
      if (status === "completed") return '<span class="status-tag status-completed">Terminé</span>';
      if (status === "cancelled") return '<span class="status-tag status-cancelled">Annulé</span>';
      return '<span class="status-tag status-upcoming">À venir</span>';
    }

    function renderDays(data) {
      var html = "";
      data.weeks.forEach(function (week) {
        week.forEach(function (cell) {
          var cls = "day-cell";
          if (!cell.in_month) cls += " other-month";
          if (cell.events.length) cls += " has-event";
          if (cell.date === data.selected_date) cls += " selected";
          if (cell.is_today && cell.date !== data.selected_date) cls += " today";

          var year = cell.date.slice(0, 4);
          var month = parseInt(cell.date.slice(5, 7), 10);
          var href = CALENDAR_URL + "?year=" + year + "&month=" + month + "&day=" + cell.date;

          html += '<a class="' + cls + '" href="' + href + '" data-date="' + cell.date + '">';
          html += '<span class="day-num">' + cell.day + "</span>";
          html += '<span class="event-dot"></span>';
          if (cell.events.length) {
            var label = escapeHtml(cell.events[0].title);
            if (cell.events.length > 1) label += " · +" + (cell.events.length - 1);
            html += '<span class="event-pill">' + label + "</span>";
          }
          html += "</a>";
        });
      });
      daysEl.innerHTML = html;
    }

    function renderEvents(data) {
      eventsHeadingEl.textContent = "Événements du " + data.selected_date_label;

      if (!data.selected_events.length) {
        eventsListEl.innerHTML = '<div class="no-events">Aucun événement prévu ce jour-là.</div>';
        return;
      }

      var html = "";
      data.selected_events.forEach(function (e) {
        html += '<a class="event-card" href="' + eventUrl(e.id) + '">';
        html += '<div class="event-body">';
        html += '<div class="time bottom">' + escapeHtml(e.time_label || "Toute la journée") + "</div>";
        html += '<div class="title-row"><div class="title">' + escapeHtml(e.title) + "</div>" + statusTag(e.status) + "</div>";
        if (e.description) html += '<p class="description">' + escapeHtml(e.description) + "</p>";
        if (e.location) {
          html += '<div class="location"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>';
          html += escapeHtml(e.location) + (e.department ? " · " + escapeHtml(e.department) : "") + "</div>";
        }
        html += "</div></a>";
      });
      eventsListEl.innerHTML = html;
    }

    function updateNav(data) {
      monthLabelEl.textContent = data.month_label;

      navPrevYear.href = CALENDAR_URL + "?year=" + (data.year - 1) + "&month=" + data.month;
      navPrevYear.dataset.year = data.year - 1;
      navPrevYear.dataset.month = data.month;

      navPrevMonth.href = CALENDAR_URL + "?year=" + data.prev_year + "&month=" + data.prev_month;
      navPrevMonth.dataset.year = data.prev_year;
      navPrevMonth.dataset.month = data.prev_month;

      navNextMonth.href = CALENDAR_URL + "?year=" + data.next_year + "&month=" + data.next_month;
      navNextMonth.dataset.year = data.next_year;
      navNextMonth.dataset.month = data.next_month;

      navNextYear.href = CALENDAR_URL + "?year=" + (data.year + 1) + "&month=" + data.month;
      navNextYear.dataset.year = data.year + 1;
      navNextYear.dataset.month = data.month;
    }

    function render(data, pushState) {
      updateNav(data);
      renderDays(data);
      renderEvents(data);
      if (pushState !== false) {
        var url = CALENDAR_URL + "?year=" + data.year + "&month=" + data.month + "&day=" + data.selected_date;
        history.pushState({ year: data.year, month: data.month, day: data.selected_date }, "", url);
      }
    }

    function skeletonEvents(count) {
      var html = "";
      for (var i = 0; i < count; i++) {
        html +=
          '<div class="event-card skeleton-event">' +
          '<span class="skeleton-bar sk-time"></span>' +
          '<div class="event-body">' +
          '<span class="skeleton-bar sk-title"></span>' +
          '<span class="skeleton-bar sk-line"></span>' +
          '<span class="skeleton-bar sk-line short"></span>' +
          "</div></div>";
      }
      return html;
    }

    function load(year, month, day, pushState) {
      daysEl.classList.add("loading");
      eventsListEl.innerHTML = skeletonEvents(2);
      var url = EVENTS_URL + "?year=" + year + "&month=" + month + (day ? "&day=" + day : "");
      fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(function (res) {
          if (!res.ok) throw new Error("network");
          return res.json();
        })
        .then(function (data) {
          render(data, pushState);
        })
        .catch(function () {
          // Repli : navigation classique si le fetch échoue
          window.location.href = CALENDAR_URL + "?year=" + year + "&month=" + month + (day ? "&day=" + day : "");
        })
        .finally(function () {
          daysEl.classList.remove("loading");
        });
    }

    // Boutons de navigation (année précédente/suivante, mois précédent/suivant, aujourd'hui)
    document.querySelectorAll(".month-nav a[data-year]").forEach(function (link) {
      link.addEventListener("click", function (ev) {
        ev.preventDefault();
        load(parseInt(this.dataset.year, 10), parseInt(this.dataset.month, 10), this.dataset.day || null);
      });
    });

    // Clic sur un jour
    daysEl.addEventListener("click", function (ev) {
      var cell = ev.target.closest(".day-cell");
      if (!cell) return;
      ev.preventDefault();
      var d = cell.dataset.date;
      var year = parseInt(d.slice(0, 4), 10);
      var month = parseInt(d.slice(5, 7), 10);
      load(year, month, d);
    });

    // Bouton précédent/suivant du navigateur
    window.addEventListener("popstate", function (ev) {
      if (ev.state) {
        load(ev.state.year, ev.state.month, ev.state.day, false);
      }
    });

    // Permet au bouton retour de revenir au tout premier état affiché
    if (window.location.search) {
      var params = new URLSearchParams(window.location.search);
      history.replaceState(
        {
          year: parseInt(params.get("year"), 10) || undefined,
          month: parseInt(params.get("month"), 10) || undefined,
          day: params.get("day") || undefined,
        },
        "",
        window.location.href
      );
    }
  })();
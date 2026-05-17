"""
ZiggoGo EPG

XML TV structure writer
"""

import json
import logging
import sqlite3

from lxml import etree


class XMLTVWriter:
    """Write XMLTV data from database"""

    DVB_PRIORITY = {
        # Subcategorie: Hoofdcategorie (subcategorie wint)
        "Detective / Thriller": "Movie / Drama",
        "Adventure / Western / War": "Movie / Drama",
        "Science fiction / Fantasy / Horror": "Movie / Drama",
        "Comedy": "Movie / Drama",
        "Soap / Melodrama / Folkloric": "Movie / Drama",
        "Romance": "Movie / Drama",
        "Serious / Classical / Religious / Historical movie / Drama": "Movie / Drama",
        "Adult movie / Drama": "Movie / Drama",
        "Talk show": "Show / Game show",
        "Game show / Quiz / Contest": "Show / Game show",
        "Variety show": "Show / Game show",
        "Football / Soccer": "Sports",
        "Team sports (excluding football)": "Sports",
        "Individual sports": "Sports",
        "Athletics": "Sports",
        "Motor sport": "Sports",
        "Water sport": "Sports",
        "Equestrian": "Sports",
        "Martial sports": "Sports",
        "Sports magazines": "Sports",
        "Fitness and health": "Sports",
        "Special events (Olympic Games; World Cup; etc.)": "Sports",
        "News / Weather report": "News / Current affairs",
        "Discussion / Interview / Debate": "News / Current affairs",
        "Ballet": "Music / Ballet / Dance",
        "Rock / Pop": "Music / Ballet / Dance",
        "Musical / Opera": "Music / Ballet / Dance",
        "Performing arts": "Arts / Culture",
        "Fine arts": "Arts / Culture",
        "Religion": "Arts / Culture",
        "Popular culture / Traditional arts": "Arts / Culture",
        "Literature": "Arts / Culture",
        "Handicraft": "Arts / Culture",
        "Fashion": "Arts / Culture",
        "Motoring": "Arts / Culture",
        "Tourism / Travel": "Arts / Culture",
        "Cooking": "Arts / Culture",
        "Gardening": "Arts / Culture",
        "Leisure hobbies": "Arts / Culture",
        "Advertisement / Shopping": "Arts / Culture",
        "Education / Science / Factual topics": "Social / Political issues / Economics",
        "Nature / Animals / Environment": "Social / Political issues / Economics",
        "Technology / Natural sciences": "Social / Political issues / Economics",
        "Medicine / Physiology / Psychology": "Social / Political issues / Economics",
        "Economics / Social advisory": "Social / Political issues / Economics",
        "Remarkable people": "Social / Political issues / Economics",
        "Informational / Educational / School programs": "Social / Political issues / Economics",
        "Magazines / Reports / Documentary": "Social / Political issues / Economics",
    }

    GENRE_MAP = {
        # Film
        "Film": "Movie / Drama",
        "Actie": "Adventure / Western / War",
        "Avontuur": "Adventure / Western / War",
        "Animatie": "Cartoons / Puppets",
        "Anime": "Cartoons / Puppets",
        "Komedie": "Comedy",
        "Romantische komedie": "Comedy",
        "Standup komedie": "Comedy",
        "Zwarte komedie": "Comedy",
        "Sitcoms": "Comedy",
        "Documentaire": "Documentary",
        "Docudrama": "Documentary",
        "Docusoap": "Documentary",
        "Drama": "Movie / Drama",
        "Dramaseries": "Movie / Drama",
        "Historisch drama": "Serious / Classical / Religious / Historical movie / Drama",
        "Misdaaddrama": "Detective / Thriller",
        "Miniseries": "Movie / Drama",
        "Fantasy": "Science fiction / Fantasy / Horror",
        "Sciencefiction": "Science fiction / Fantasy / Horror",
        "Horror": "Science fiction / Fantasy / Horror",
        "Thriller": "Detective / Thriller",
        "Mysterie": "Detective / Thriller",
        "Misdaad": "Detective / Thriller",
        "Romantiek": "Romance",
        "Western": "Adventure / Western / War",
        "Oorlog": "Adventure / Western / War",
        "Musical": "Musical / Opera",
        "Biografie": "Documentary",
        # Nieuws & Actualiteit
        "Nieuws": "News / Current affairs",
        "Actualiteit": "News / Current affairs",
        "Actualiteitenprogramma's": "News / Current affairs",
        "Debat": "Discussion / Interview / Debate",
        "Politiek": "Social / Political issues / Economics",
        "Politieke satire": "Social / Political issues / Economics",
        "Interview": "Discussion / Interview / Debate",
        "Business & Financial": "News / Current affairs",
        "Weer": "News / Weather report",
        # Sport
        "Sport": "Sports",
        "Voetbal": "Football / Soccer",
        "American football": "Team sports (excluding football)",
        "Basketbal": "Team sports (excluding football)",
        "Tennis": "Tennis / Squash",
        "Golf": "Sports",
        "Atletiek": "Athletics",
        "Wielrennen": "Sports",
        "Motorsport": "Motor sport",
        "Motorracen": "Motor sport",
        "Rugby": "Team sports (excluding football)",
        "Rugby League": "Team sports (excluding football)",
        "Rugby Union": "Team sports (excluding football)",
        "Honkbal": "Team sports (excluding football)",
        "Cricket": "Team sports (excluding football)",
        "Volleybal": "Team sports (excluding football)",
        "Darts": "Sports",
        "Snooker": "Sports",
        "Paardensport": "Equestrian",
        "Zeilen": "Water sport",
        "Skateboarden": "Sports",
        "Extreme sporten": "Sports",
        "Vliegsport": "Sports",
        "Mixed Martial Arts (MMA)": "Martial sports",
        "Running": "Athletics",
        "Stierenvechten": "Sports",
        "Cheerleading": "Sports",
        "Competitiesporten": "Sports",
        "Multisportevenement": "Special events (Olympic Games; World Cup; etc.)",
        "Sporttalkshow": "Sports magazines",
        "Exercise": "Fitness and health",
        "Outdoor": "Sports",
        # Kinderen
        "Kinderen": "Children's / Youth programs",
        "Kids en familie": "Children's / Youth programs",
        # Muziek
        "Muziek": "Music / Ballet / Dance",
        "Ballet": "Ballet",
        "Dans": "Music / Ballet / Dance",
        "Opera": "Musical / Opera",
        "Podiumkunsten": "Performing arts",
        "Awards": "Music / Ballet / Dance",
        # Kunst & Cultuur
        "Beeldende kunst": "Fine arts",
        "Kunstnijverheid": "Handicraft",
        "Boeken & literatuur": "Literature",
        "Religie": "Religion",
        "Geschiedenis": "Documentary",
        "Bloemlezing": "Arts / Culture (without music)",
        # Sociale & Maatschappelijke onderwerpen
        "Samenleving": "Social / Political issues / Economics",
        "Educatie": "Informational / Educational / School programs",
        "Wetenschap": "Education / Science / Factual topics",
        "Natuur": "Nature / Animals / Environment",
        "Natuur en milieu": "Nature / Animals / Environment",
        "Technologie": "Technology / Natural sciences",
        "Dieren": "Nature / Animals / Environment",
        "Gezondheid": "Medicine / Physiology / Psychology",
        "Medisch": "Medicine / Physiology / Psychology",
        "Opvoeden": "Informational / Educational / School programs",
        "LHBTI": "Social / Political issues / Economics",
        "Recht": "Social / Political issues / Economics",
        "Paranormaal": "Detective / Thriller",
        "Landbouw": "Nature / Animals / Environment",
        # Lifestyle
        "Reizen": "Tourism / Travel",
        "Culinair": "Cooking",
        "Mode": "Fashion",
        "Bouwen en verbouwen": "Leisure hobbies",
        "Doe-het-zelf": "Leisure hobbies",
        "Home & Garden": "Gardening",
        "Shoppen": "Advertisement / Shopping",
        "Verzamelen": "Leisure hobbies",
        "Veiling": "Advertisement / Shopping",
        "Auto's": "Motoring",
        "Motors": "Motoring",
        # Entertainment & Shows
        "Gamen": "Game show / Quiz / Contest",
        "Entertainment": "Show / Game show",
        "Variété": "Variety show",
        "Spelshow": "Game show / Quiz / Contest",
        "Talkshow": "Talk show",
        "Reality": "Variety show",
        "Reality-competitie": "Game show / Quiz / Contest",
        "Event": "Show / Game show",
        "Consumentenprogramma's": "Show / Game show",
        "Soap": "Soap / Melodrama / Folkloric",
        "Erotiek": "Adult movie / Drama",
        "Erotisch": "Adult movie / Drama",
    }


    def __init__(self, database_connection: sqlite3.Connection):
        """
        Initialize XMLTVWriter.

        :param database_connection: An opened SQLite database connection to the EPG data
        """
        self._db = database_connection
        self._dbcur = self._db.cursor()

        # NL is hardcoded as it is the only language ZiggoGo provides.
        self._lang = "nl"

    def generate_xmltv(self) -> bytes:
        """
        Generate the XMLTV file from the database.
        :return: The XMLTV data as a string
        """

        logging.info("Generating XMLTV data...")

        xmltv = etree.Element(
            "tv",
            attrib={
                "source-info-url": "https://www.ziggogo.tv",
                "source-info-name": "ZiggoGo",
                "generator-info-name": "ZiggoGo EPG",
                "generator-info-url": "https://github.com/jbogers/ziggogo-epg",
            },
        )

        self._add_channels(xmltv=xmltv)
        self._add_programmes(xmltv=xmltv)

        return etree.tostring(xmltv, pretty_print=True)

    def _add_channels(self, xmltv: etree.Element):
        """Add the channels to the XMLTV element"""

        self._dbcur.execute("SELECT id, name, logo FROM channels")

        for row in self._dbcur:
            channel = etree.SubElement(xmltv, "channel", attrib={"id": row["id"].replace("_", ".")})
            etree.SubElement(channel, "display-name", attrib={"lang": self._lang}).text = row["name"]

            if row["logo"]:
                etree.SubElement(channel, "icon", attrib={"src": row["logo"]})

    def _add_programmes(self, xmltv: etree.Element):
        """Add the programmes to XMLTV element"""

        self._dbcur.execute(
            "SELECT channelid, title, starttime, endtime, pd.details AS details FROM programmes p "
            "LEFT JOIN programmedetails pd ON pd.id = p.id"
        )

        for row in self._dbcur:
            programme = etree.SubElement(
                xmltv,
                "programme",
                attrib={"start": row["starttime"], "stop": row["endtime"], "channel": row["channelid"].replace("_", ".")},
            )
            etree.SubElement(programme, "title", attrib={"lang": self._lang}).text = row["title"]

            if row["details"] is not None:
                details = json.loads(row["details"])

                if "sub-title" in details:
                    etree.SubElement(programme, "sub-title", attrib={"lang": self._lang}).text = details["sub-title"]

                if "desc" in details:
                    etree.SubElement(programme, "desc", attrib={"lang": self._lang}).text = details["desc"]

                if "credits" in details:
                    credits = etree.SubElement(programme, "credits")
                    if "directors" in details["credits"]:
                        for director in details["credits"]["directors"]:
                            etree.SubElement(credits, "director").text = director
                    if "actors" in details["credits"]:
                        for actor in details["credits"]["actors"]:
                            etree.SubElement(credits, "actor").text = actor
                    if "producers" in details["credits"]:
                        for producers in details["credits"]["producers"]:
                            etree.SubElement(credits, "producer").text = producers

                if "date" in details:
                    etree.SubElement(programme, "date").text = details["date"]

                if "categories" in details:
                    # Verzamel alle DVB codes
                    dvb_codes = set()
                    for category in details["categories"]:
                        dvb_code = self.GENRE_MAP.get(category)
                        if dvb_code:
                            dvb_codes.add(dvb_code)
                    # Verwijder hoofdcategorieen als subcategorie aanwezig is
                    to_remove = set()
                    for code in dvb_codes:
                        parent = self.DVB_PRIORITY.get(code)
                        if parent and parent in dvb_codes:
                            to_remove.add(parent)
                    dvb_codes -= to_remove
                    # Schrijf alleen de meest specifieke categorie weg (maximaal 1)
                    if dvb_codes:
                        etree.SubElement(programme, "category", attrib={"lang": "en"}).text = next(iter(dvb_codes))

                if "country" in details:
                    etree.SubElement(programme, "country").text = details["country"]

                if "episode" in details:
                    season = None
                    ziggo_internal_id = False
                    try:
                        season = int(details["episode"]["season"]) - 1
                        if season >= 99999:
                            # Fake season number used in ZiggoGo that should never be displayed
                            ziggo_internal_id = True
                    except (KeyError, ValueError):
                        # No season value or not an integer
                        pass
                    episode = None
                    try:
                        episode = int(details["episode"]["episode"]) - 1
                        if episode >= 9999999:
                            # Fake episode number used in ZiggoGo that should never be displayed
                            ziggo_internal_id = True
                    except (KeyError, ValueError):
                        # No season value or not an integer
                        pass
                    if not ziggo_internal_id and (season is not None or episode is not None):
                        season_str = str(season) if season is not None else ""
                        episode_str = str(episode) if episode is not None else ""
                        etree.SubElement(programme, "episode-num", attrib={"system": "xmltv_ns"}).text = f"{season_str}.{episode_str}."
                
                if "img" in details:
                    etree.SubElement(programme, "icon", attrib={"src": details["img"]})

                if "rating" in details:
                    rating = etree.SubElement(programme, "rating", attrib={"system": "Kijkwijzer"})
                    etree.SubElement(rating, "value").text = details["rating"]

    def __del__(self):
        """Cleanup"""
        self._dbcur.close()

import requests
import datetime
import re
from bs4 import BeautifulSoup as bs

skillshot_url: str = "https://www.skillshot.pl/"

def get_hits_from_skillshot() -> list[tuple[str]]:
    page = requests.get(skillshot_url)


    soup = bs(page.content, 'html.parser')
    list_table_tag = soup.find_all('tr')
    notif_info = []

    hits_today = []

    for row in list_table_tag:
        notif_info = row.find_all('td')
        text_split = notif_info[1].get_text().split('\n')
        
        job_url = skillshot_url[0:-1] + row.find('a', href=True)['href']
        contract_type = row.find('span').get_text()
        role = row.find('a').get_text()
        company = text_split[2].lstrip()
        location = text_split[4].lstrip()
        date = notif_info[2].get_text()

        role_regex = re.compile(".*prak|staż|juni|inter", re.IGNORECASE)

        discord_message_tpl = f"> :clipboard: **Rodzaj umowy:** {contract_type}\n> :office: **Firma:** {company}\n> :map: **Lokalizacja:** {location}\n> :date: **Data dodania:** {date}\n> :link: **Link:** <{job_url}>\n~~                     ~~\n"
        
        

        if re.search(role_regex, role):
            discord_message_tpl = "## :warning: Entry level! :warning:\n" + discord_message_tpl


        dt_date = datetime.datetime.strptime(date, '%Y-%m-%d')

        if dt_date == datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0):
            hits_today.append((role, discord_message_tpl))

    return hits_today

import requests
import datetime
import re
from bs4 import BeautifulSoup as bs


def get_hits_from_skillshot(pages: int, date_to_compare: datetime.datetime) -> list[tuple[str, str, datetime.datetime, str, str]]:
    """
    Scrap skillshot.pl for today's job offers

    :param int pages: number of pages to scrape
    :param datetime.datetime date_to_compare: earliest date to compare job offers against

    :return: list of tuples with the following structure:
                (role, discord_message_tpl, dt_date, company, location)
    :rtype: list[tuple[str, str, datetime.datetime, str, str]]
    """

    skillshot_url: str = "https://www.skillshot.pl/jobs?page={pg_num}"
    hits_today = []

    for pg_num in range(1, pages + 1):
        page = requests.get(skillshot_url.format(pg_num=pg_num))

        soup = bs(page.content.decode('utf-8'), 'html.parser')
        list_table_tag = soup.find_all('tr')
        notif_info = []


        for row in list_table_tag:
            notif_info = row.find_all('td')
            text_split = notif_info[1].get_text().split('\n')
            
            job_url = skillshot_url[0:-19] + row.find('a', href=True)['href']
            contract_type = row.find('span').get_text()
            role = row.find('a').get_text()
            company = text_split[2].lstrip()
            location = text_split[4].lstrip()
            date = notif_info[2].get_text()

            discord_message_tpl = f"> :clipboard: **Rodzaj umowy:** {contract_type}\n> :office: **Firma:** {company}\n> :map: **Lokalizacja:** {location}\n> :date: **Data dodania:** {date}\n> :link: **Link:** <{job_url}>\n~~                     ~~\n"
            
            role_regex = re.compile(".*prak|staż|juni|inter", re.IGNORECASE)
            if re.search(role_regex, role):
                discord_message_tpl = "## :warning: Entry level! :warning:\n" + discord_message_tpl

            dt_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            if dt_date >= date_to_compare:
                hits_today.append((role, discord_message_tpl, dt_date, company, location))


    return hits_today

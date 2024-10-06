# ContentDB
# Copyright (C) 2021 rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional

import requests

from app import app
from app.models import User
from app.tasks import celery


@celery.task()
def post_discord_webhook(username: Optional[str], content: str, is_queue: bool, title: Optional[str] = None, description: Optional[str] = None, thumbnail: Optional[str] = None):
	discord_urls = app.config.get("DISCORD_WEBHOOK_QUEUE" if is_queue else "DISCORD_WEBHOOK_FEED")
	if discord_urls is None:
		return

	if isinstance(discord_urls, str):
		discord_urls = [discord_urls]

	json = {
		"content": content[0:2000],
	}

	if username:
		json["username"] = username[0:80]
		user = User.query.filter_by(username=username).first()
		if user:
			json["avatar_url"] = user.get_profile_pic_url().replace("/./", "/")
			if json["avatar_url"].startswith("/"):
				json["avatar_url"] = app.config["BASE_URL"] + json["avatar_url"]

	if title:
		embed = {
			"title": title[0:256],
			"description": description[0:4000],
		}

		if thumbnail:
			embed["thumbnail"] = {"url": thumbnail}

		json["embeds"] = [embed]

	for url in discord_urls:
		res = requests.post(url, json=json, headers={"Accept": "application/json"})
		if not res.ok:
			raise Exception(f"Failed to submit Discord webhook {res.json}")
		res.raise_for_status()

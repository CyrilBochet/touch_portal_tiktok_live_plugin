import sys
import json
import asyncio
import threading
import re
import requests
from datetime import datetime
from collections import defaultdict
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent, CommentEvent, GiftEvent,
    DiggEvent, LikeEvent, RoomUserSeqEvent,
    FollowEvent, ShareEvent, QuestionNewEvent,
    JoinEvent, LiveEndEvent
)

class TikTokLivePlugin:
    def __init__(self):
        self.client = None
        self.monitoring = False
        self.current_username = ""
        self.total_likes = 0
        self.user_likes = defaultdict(int)
        self.initial_followers = 0
        self.loop = None
        self.monitor_thread = None
        
    def send_tp_message(self, message_type, data=None):
        """Envoie un message à TouchPortal"""
        message = {"type": message_type}
        if data:
            message.update(data)
        print(json.dumps(message), flush=True)
    
    def update_state(self, state_id, value):
        """Met à jour un état TouchPortal"""
        self.send_tp_message("stateUpdate", {
            "id": state_id,
            "value": str(value)
        })
    
    def trigger_event(self, event_id, data=None):
        """Déclenche un événement TouchPortal"""
        message = {"type": "broadcast", "event": event_id}
        if data:
            message.update(data)
        print(json.dumps(message), flush=True)

    def fetch_tiktok_followers(self, username: str) -> int:
        """Récupère le nombre de followers"""
        url = f"https://www.tiktok.com/@{username}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            match = re.search(r'"followerCount":(\d+)', resp.text)
            return int(match.group(1)) if match else 0
        except requests.RequestException:
            return 0

    async def start_monitoring(self, username):
        """Démarre le monitoring d'un utilisateur TikTok"""
        if self.monitoring:
            await self.stop_monitoring()
        
        self.current_username = username.lstrip('@')
        self.client = TikTokLiveClient(unique_id=self.current_username)
        self.total_likes = 0
        self.user_likes.clear()
        self.initial_followers = self.fetch_tiktok_followers(self.current_username)
        
        # Configuration des événements
        self.setup_event_handlers()
        
        try:
            self.monitoring = True
            self.update_state("tiktok.live.status", "Connecting...")
            self.update_state("tiktok.live.current_username", self.current_username)
            self.update_state("tiktok.live.followers", self.initial_followers)
            
            await self.client.start()
        except Exception as e:
            self.monitoring = False
            self.update_state("tiktok.live.status", f"Error: {str(e)}")

    async def stop_monitoring(self):
        """Arrête le monitoring"""
        if self.client and self.monitoring:
            await self.client.stop()
        self.monitoring = False
        self.update_state("tiktok.live.status", "Stopped")
        self.reset_states()

    def setup_event_handlers(self):
        """Configure les gestionnaires d'événements TikTok"""
        
        @self.client.on(ConnectEvent)
        async def on_connect(event):
            self.update_state("tiktok.live.status", "Connected")
            self.update_state("tiktok.live.room_id", str(self.client.room_id))
            self.trigger_event("tiktok.live.connected")

        @self.client.on(CommentEvent)
        async def on_comment(event):
            self.update_state("tiktok.live.last_comment", event.comment)
            self.update_state("tiktok.live.last_commenter", event.user.nickname)
            self.trigger_event("tiktok.live.new_comment")

        @self.client.on(GiftEvent)
        async def on_gift(event):
            gift = event.gift
            count = getattr(gift, 'repeat_count', getattr(gift, 'repeatCount', 1)) or 1
            name = getattr(gift, 'name', getattr(gift, 'giftName', ''))
            value = gift.diamond_count * count
            self.trigger_event("tiktok.live.gift_received", {
                "gift_name": name,
                "count": count,
                "value": value,
                "sender": event.user.nickname
            })

        @self.client.on(DiggEvent)
        async def on_digg(event):
            count = getattr(event, 'digg_count', getattr(event, 'diggCount', 1)) or 1
            self.total_likes += count
            self.user_likes[event.user.unique_id] += count
            self.update_state("tiktok.live.total_likes", self.total_likes)

        @self.client.on(LikeEvent)
        async def on_like(event):
            self.total_likes += 1
            self.user_likes[event.user.unique_id] += 1
            self.update_state("tiktok.live.total_likes", self.total_likes)

        @self.client.on(RoomUserSeqEvent)
        async def on_viewers(event):
            viewers = getattr(event, 'total_user', 0)
            current_followers = self.fetch_tiktok_followers(self.current_username)
            self.update_state("tiktok.live.viewers", viewers)
            self.update_state("tiktok.live.followers", current_followers)

        @self.client.on(FollowEvent)
        async def on_follow(event):
            self.trigger_event("tiktok.live.new_follower", {
                "follower": event.user.nickname
            })

        @self.client.on(ShareEvent)
        async def on_share(event):
            pass  # Peut être utilisé pour d'autres fonctionnalités

        @self.client.on(QuestionNewEvent)
        async def on_question(event):
            self.update_state("tiktok.live.last_comment", f"Q: {event.question}")
            self.update_state("tiktok.live.last_commenter", event.user.nickname)

        @self.client.on(JoinEvent)
        async def on_join(event):
            pass  # Peut être utilisé pour d'autres fonctionnalités

        @self.client.on(LiveEndEvent)
        async def on_end(event):
            final_followers = self.fetch_tiktok_followers(self.current_username)
            self.update_state("tiktok.live.followers", final_followers)
            self.update_state("tiktok.live.status", "Stream Ended")
            self.trigger_event("tiktok.live.stream_ended")
            self.monitoring = False

    def reset_states(self):
        """Remet à zéro tous les états"""
        self.update_state("tiktok.live.current_username", "")
        self.update_state("tiktok.live.viewers", "0")
        self.update_state("tiktok.live.total_likes", "0")
        self.update_state("tiktok.live.followers", "0")
        self.update_state("tiktok.live.last_comment", "")
        self.update_state("tiktok.live.last_commenter", "")
        self.update_state("tiktok.live.room_id", "")

    def run_async_in_thread(self, coro):
        """Exécute une coroutine dans un thread séparé"""
        def run_in_thread():
            if self.loop is None or self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(coro)
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            # Arrêter le thread précédent
            if self.loop:
                self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self.stop_monitoring()))
        
        self.monitor_thread = threading.Thread(target=run_in_thread, daemon=True)
        self.monitor_thread.start()

    def handle_tp_message(self, message):
        """Traite les messages reçus de TouchPortal"""
        msg_type = message.get("type")
        
        if msg_type == "info":
            # TouchPortal demande des informations sur le plugin
            self.send_tp_message("info", {
                "sdkVersion": 6,
                "version": "1.0.0",
                "plugin": "TikTok Live Monitor"
            })
            
        elif msg_type == "settings":
            # Initialisation des états
            self.reset_states()
            self.update_state("tiktok.live.status", "Ready")
            
        elif msg_type == "action":
            action_id = message.get("actionId")
            
            if action_id == "tiktok.live.start":
                data = message.get("data", [])
                username = ""
                for item in data:
                    if item.get("id") == "tiktok.live.username":
                        username = item.get("value", "")
                        break
                
                if username:
                    self.run_async_in_thread(self.start_monitoring(username))
                else:
                    self.update_state("tiktok.live.status", "Error: No username provided")
                    
            elif action_id == "tiktok.live.stop":
                self.run_async_in_thread(self.stop_monitoring())

    def run(self):
        """Boucle principale du plugin"""
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    message = json.loads(line.strip())
                    self.handle_tp_message(message)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    # Log l'erreur mais continue
                    self.send_tp_message("error", {"message": str(e)})
                    
        except KeyboardInterrupt:
            pass
        finally:
            if self.monitoring:
                self.run_async_in_thread(self.stop_monitoring())

def main():
    plugin = TikTokLivePlugin()
    plugin.run()

if __name__ == "__main__":
    main()
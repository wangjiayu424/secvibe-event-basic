"""Stage 1: public events and persisted registration. Local filming use."""
import argparse
import datetime
import json
from pathlib import Path
from common import APIError, DemoHandler, connect, email, launch, new_id, text

ROOT = Path(__file__).resolve().parent


def seed(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    with connect(data_dir / 'demo.sqlite3') as db:
        db.executescript((ROOT / 'schema.sql').read_text())
        if not db.execute('SELECT count(*) FROM events').fetchone()[0]:
            events = json.loads((ROOT / 'seed.json').read_text())['events']
            for event in events:
                db.execute('INSERT INTO events(id,title,subtitle,category,starts_at,location,capacity,description) VALUES(:id,:title,:subtitle,:category,:starts_at,:location,:capacity,:description)', event)
            db.execute('INSERT INTO registrations VALUES(?,?,?,?,?)', ('BM-DEMO001', 'evt-build', '演示访客', 'guest@example.test', '2026-10-28T10:00:00+08:00'))


class Handler(DemoHandler):
    def handle_api(self, method):
        path = self.route_path
        if method == 'GET' and path == '/api/health':
            return self.respond({'app': 'makers-local', 'stage': 'basic'})
        if method == 'GET' and path == '/api/session':
            return self.respond({'stage': 'basic', 'user': None, 'csrf': self.session['csrf']})
        if method == 'GET' and path == '/api/events':
            with self.db() as db:
                rows = db.execute('SELECT e.*, (SELECT count(*) FROM registrations r WHERE r.event_id=e.id) AS registered FROM events e ORDER BY starts_at,id').fetchall()
            return self.respond({'events': [dict(row) for row in rows]})
        if method == 'POST' and path == '/api/registrations':
            data = self.read_json()
            event_id = text(data, 'event_id', 1, 50)
            name = text(data, 'display_name', 1, 40)
            address = email(data)
            with self.db() as db:
                db.execute('BEGIN IMMEDIATE')
                event = db.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
                if not event:
                    raise APIError(404, '活动不存在。')
                if db.execute('SELECT 1 FROM registrations WHERE event_id=? AND email=?', (event_id, address)).fetchone():
                    raise APIError(409, '这个邮箱已经报名该活动。', 'email')
                count = db.execute('SELECT count(*) FROM registrations WHERE event_id=?', (event_id,)).fetchone()[0]
                if count >= event['capacity']:
                    raise APIError(409, '本场名额已满，请选择其他活动。')
                registration = {'id': new_id('BM-'), 'event_id': event_id, 'display_name': name, 'email': address,
                                'created_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')}
                db.execute('INSERT INTO registrations(id,event_id,display_name,email,created_at) VALUES(:id,:event_id,:display_name,:email,:created_at)', registration)
            return self.respond({'registration': registration}, 201)
        raise APIError(404, '没有找到这个接口。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8761)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'local_data')
    parser.add_argument('--seed-only', action='store_true')
    args = parser.parse_args()
    seed(args.data_dir)
    if not args.seed_only:
        launch(Handler, ROOT, args.data_dir, args.port, 'makers_basic', 'basic')

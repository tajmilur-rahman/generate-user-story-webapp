#!/usr/bin/env python
"""
Create a password account, or set the password on an existing one.

There is no public sign-up route: the demo instance is reachable from the
internet, so accounts are issued here instead.

    python scripts/create_user.py alice@example.com
    python scripts/create_user.py alice@example.com --name "Alice Smith"
    python scripts/create_user.py alice@example.com --password hunter2
    python scripts/create_user.py --bulk 10          # survey reviewer accounts
    python scripts/create_user.py --list

Omitting --password prompts for one without echoing it, which keeps the
password out of your shell history. Run from the project root.
"""
import argparse
import csv
import getpass
import os
import secrets
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from backend.app import app  # noqa: E402  (needs sys.path set first)
from backend.models import User, db  # noqa: E402

MIN_PASSWORD_LENGTH = 8


def read_password(supplied):
    if supplied:
        return supplied

    first = getpass.getpass('Password: ')
    second = getpass.getpass('Confirm password: ')
    if first != second:
        sys.exit('Passwords do not match.')
    return first


def list_users():
    users = User.query.order_by(User.email).all()
    if not users:
        print('No accounts yet.')
        return

    print(f'{len(users)} account(s):')
    for user in users:
        methods = []
        if user.has_password:
            methods.append('password')
        if user.google_id:
            methods.append('google')
        print(f'  {user.email:<40} {", ".join(methods) or "no sign-in method"}')


def upsert(email, password, name):
    email = email.strip().lower()
    if not email:
        sys.exit('Email must not be empty.')
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f'Password must be at least {MIN_PASSWORD_LENGTH} characters.')

    user = User.query.filter(db.func.lower(User.email) == email).first()

    if user:
        user.set_password(password)
        if name:
            user.name = name
        db.session.commit()
        print(f'Updated password for {email}')
    else:
        user = User(email=email, name=name or email.split('@')[0])
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Created {email}')


def generate_password():
    """
    A readable but strong password: four 4-character groups.

    Survey reviewers type these by hand off a sheet of paper, so the alphabet
    drops the characters that get misread -- 0/O, 1/l/I. 20 chars from a
    31-symbol alphabet is still ~99 bits of entropy.
    """
    alphabet = 'abcdefghijkmnpqrstuvwxyz23456789'
    groups = ['' .join(secrets.choice(alphabet) for _ in range(4)) for _ in range(4)]
    return '-'.join(groups)


def create_batch(prefix, count, domain, out_path):
    """Create count accounts and write their credentials to a CSV."""
    rows = []
    for n in range(1, count + 1):
        email = f'{prefix}{n:02d}@{domain}'.lower()
        password = generate_password()
        name = f'{prefix.capitalize()} {n:02d}'

        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user is None:
            user = User(email=email, name=name)
            db.session.add(user)
        user.set_password(password)
        if not user.name:
            user.name = name
        rows.append((email, password, name))

    db.session.commit()

    with open(out_path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['email', 'password', 'name'])
        writer.writerows(rows)

    print(f'Created/updated {len(rows)} accounts. Credentials written to {out_path}')
    print('This file is the only copy of these passwords -- they are stored hashed.')
    print()
    for email, password, _ in rows:
        print(f'  {email:<34} {password}')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('email', nargs='?', help='account email address')
    parser.add_argument('--password', help='password (prompted for if omitted)')
    parser.add_argument('--name', help='display name')
    parser.add_argument('--list', action='store_true', help='list accounts and exit')
    parser.add_argument('--bulk', type=int, metavar='N',
                        help='create N numbered accounts instead of one')
    parser.add_argument('--prefix', default='reviewer',
                        help='email prefix for --bulk (default: reviewer)')
    parser.add_argument('--domain', default='geneus.local',
                        help='email domain for --bulk (default: geneus.local)')
    parser.add_argument('--out', default='reviewer-accounts.csv',
                        help='where --bulk writes the credential CSV')
    args = parser.parse_args()

    with app.app_context():
        if args.list:
            list_users()
            return
        if args.bulk:
            if args.bulk < 1:
                parser.error('--bulk must be at least 1')
            create_batch(args.prefix, args.bulk, args.domain, args.out)
            return
        if not args.email:
            parser.error('email is required unless --list or --bulk is given')
        upsert(args.email, read_password(args.password), args.name)


if __name__ == '__main__':
    main()

"""Inspect actual graph IDs. Historical records are inert, even after forgetting."""


def snapshot(session, namespace=None):
    return session.store.inspect(namespace)

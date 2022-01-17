from requests import Session

useragent = 'NicotoolspyBot @aoirint'

def create_session() -> Session:
    session = Session()
    session.headers['User-Agent'] = useragent

    return session

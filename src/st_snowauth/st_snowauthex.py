from urllib.parse import urlencode
import requests
import streamlit as st
import html
from snowflake.snowpark import Session

import string
import random

_STKEY = 'SNOW_SESSION'
_DEFAULT_SECKEY = 'snowauthex'

# Global cache to stash incoming query parameters so that we can retrieve 
#  them on redirect. The `key` will be the `state` variable in the OAuth flow.
@st.cache_resource(ttl=300)
def qparms_cache(key):
    return {}

# Generate random string for `state` for OAuth flow
def string_num_generator(size):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))

# Validate we have all the config we need
def validate_config(config):
    required_config_options = [ 'authorization_endpoint', 
                                'token_endpoint',
                                'jwks_uri',
                                'redirect_uri',
                                'client_id',
                                'client_secret',
                                'scope' ]
    return all([k in config for k in required_config_options])

# Force an automatic redirect to the given URL.
def st_redirect(url):
    source = f"location.href = '{url}'"
    wrapped_source = f"(async () => {{{source}}})()"
    st.markdown(
        f"""
        <div style="display:none" id="stredirect">
            <iframe src="javascript: \
                var script = document.createElement('script'); \
                script.type = 'text/javascript'; \
                script.text = {html.escape(repr(wrapped_source))}; \
                var thisDiv = window.parent.document.getElementById('stredirect'); \
                var rootDiv = window.parent.parent.parent.parent.document.getElementById('root'); \
                rootDiv.appendChild(script); \
                thisDiv.parentElement.parentElement.parentElement.style.display = 'none'; \
            "/>
        </div>
        """, unsafe_allow_html=True
    )

# Show the Authentication link or auto-redirect
def show_auth_link(config, label, auto_redirect=False):
    print(f'AUTO_REDIRECT: {auto_redirect}')
    state_parameter = string_num_generator(15)
    query_params = urlencode({'redirect_uri': config['redirect_uri'], 'client_id': config['client_id'], 'response_type': 'code', 'state': state_parameter, 'scope': config['scope']})
    request_url = f"{config['authorization_endpoint']}?{query_params}"
    if len(st.query_params) > 0:
        qpcache = qparms_cache(state_parameter)
        qpcache.update(st.query_params.to_dict())
    if auto_redirect:
        st_redirect(request_url)

    else:
        st.markdown(f'<a href="{request_url}" target="_self">{label}</a>', unsafe_allow_html=True)
    st.stop()

# Use External OAuth to log into Snowflake and cache the session
#  in `st.session_state`
def snowauthex_session(config=None, label="Login via OAuth", auto_redirect=False):
    if not config:
        config = _DEFAULT_SECKEY
    if isinstance(config, str):
        config = st.secrets[config]
    if _STKEY in st.session_state:
        session = st.session_state[_STKEY]
        if session._conn._conn.is_closed():
            del st.session_state[_STKEY]
    if _STKEY not in st.session_state:
        if not validate_config(config):
            st.error("Invalid OAuth Configuration")
            st.stop()
        if 'code' not in st.query_params:
            show_auth_link(config, label, auto_redirect)
        code = st.query_params['code']
        state = st.query_params['state']
        st.query_params.clear()
        st.query_params.update(qparms_cache(state))
        qparms_cache(state).clear()
        theaders = {
                        'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
                    }
        tdata = {
                    'grant_type': 'authorization_code', 
                    'redirect_uri': config['redirect_uri'],
                    'client_id': config['client_id'],
                    'client_secret': config['client_secret'],
                    'scope': config['scope'],
                    'state': state,
                    'code': code,
                }
        try:
            ret = requests.post(config["token_endpoint"], headers=theaders, data=urlencode(tdata).encode("utf-8"))
            ret.raise_for_status()
        except requests.exceptions.RequestException as e:
            st.error(e)
            show_auth_link(config, label)
        token = ret.json()

        snow_configs = {
            'account': config['account'], 
            'authenticator': 'oauth',
            'token': token['access_token']
        }
        if 'connection' in config:
            snow_configs = {**config['connection'], **snow_configs}
        del token
        try:
            st.session_state[_STKEY] = Session.builder.configs(snow_configs).create()
        except Exception as e :
            st.error(f"Error connecting to Snowflake: \n{str(e)}")
            show_auth_link(config, label)

    session = st.session_state[_STKEY]
    return session
# encoding: utf-8
import sys
from urllib.parse import urlencode, parse_qsl, quote
import xbmcgui
import xbmcplugin
import requests

# Get the plugin url in plugin:// notation.
_URL = sys.argv[0]
# Get the plugin handle as an integer number.
_HANDLE = int(sys.argv[1])


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(_URL, urlencode(kwargs))


def list_mainmenu():
    xbmcplugin.setPluginCategory(_HANDLE, 'NC-Raws')
    xbmcplugin.setContent(_HANDLE, 'videos')

    list_item = xbmcgui.ListItem(label='Search')
    url = get_url(action='search')
    xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, isFolder=True)
    xbmcplugin.endOfDirectory(_HANDLE)
    return


def search():
    search_query = xbmcgui.Dialog().input('Search')

    if search_query == '':
        return

    xbmcgui.Dialog().notification('Searching', search_query)

    resp = requests.post('https://nc.raws.dev/0:search',
                         json={'q': search_query, 'password': None, 'page_token': None, 'page_index': 0})

    if resp.status_code != 200:
        xbmcgui.Dialog().notification('Error', 'Search failed')
        return

    resp_json = resp.json()
    files = resp_json['data']['files']

    xbmcplugin.setPluginCategory(_HANDLE, search_query)
    xbmcplugin.setContent(_HANDLE, 'videos')

    for file in files:
        list_item = xbmcgui.ListItem(label=file['name'])
        if 'thumbnailLink' in file:
            list_item.setArt({'thumb': file['thumbnailLink']})
        file_size = int(file['size'])
        list_item.setInfo(
            'video', {'title': file['name'], 'size': file_size})
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', video=build_video_url(file['name']))
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item)

    xbmcplugin.addSortMethod(
        _HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_HANDLE, updateListing=True)


def build_video_url(filename: str) -> str:
    # TODO parse filename
    return 'https://nc.raws.dev/0:/{}'.format(quote(filename.replace('.mp4', '.zip').replace('.mkv', '.zip')))


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'search':
            search()
        elif params['action'] == 'play':
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {}!'.format(paramstring))
    else:
        list_mainmenu()


if __name__ == '__main__':
    router(sys.argv[2][1:])

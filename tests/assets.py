# coding: utf-8
'''
Unit tests againsts the assets package.
'''

import re

import canvas.tests as cvt

from canvas.core.assets import get_asset

@cvt.test('Asset supply')
def test_asset_supply():
	with cvt.assertion('Simple assets load correctly'):
		asset = get_asset('/media/site_icon.png')
		assert asset.data is not None and 'png' in asset.mimetype

	with cvt.assertion('LESS assets retrieved as CSS'):
		asset = get_asset('/canvas.css')
		#	Check for LESS definitions.
		assert not re.search(r':\s+@', asset.data)

	with cvt.assertion('JSX retrieved as JS'):
		asset = get_asset('/canvas.js')
		assert '::include' not in asset.data

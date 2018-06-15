# coding: pyxl
'''
Unit tests on the views module.
'''

from pyxl import html

import canvas.tests as cvt

from canvas.core.views import PageView, view, alter_root_page_view

@cvt.test('Page view rendering')
def test_page_view():
    #    Create a page view alteration.
    @alter_root_page_view
    def do_test_alter(PageView):
        class CustomPageView(PageView):
            def get_title(self):
                #    Allow later tests to check the title.
                if not self.title or 'Test' not in self.title:
                    return 'Test'
                return self.title
        return CustomPageView

    @view()
    class TestView:
        def render(self):
            return <article>Test</article>

    page_view = PageView.resolved(None, None, ('test.js',))
    page_view.page_views.append(TestView())
    html_str = str(page_view.render())

    with cvt.assertion('Base alteration applied'):
        assert '<title>Test</title>' in html_str

    with cvt.assertion('Added views rendered'):
        assert '<article>Test</article>' in html_str

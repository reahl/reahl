
# To run this test do:
# nosetests -F reahl.webdev.fixtures:BrowserSetup -s --nologcapture reahl/doc_dev/tutorialtests/ajaxtests.py
#



from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import test
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath
from reahl.doc.examples.tutorial.ajax.ajax import WidgetRefreshUI


class RefreshFixture(WebFixture):
    def new_browser(self):
        return self.driver_browser
        
    def new_wsgi_app(self):
        return super(RefreshFixture, self).new_wsgi_app(site_root=WidgetRefreshUI, enable_js=True)

    def text_shows_selected(self, expected_selected):
        return self.browser.is_element_present(XPath.paragraph_containing('You selected link number %s' % expected_selected))

#------ Tests

@test(RefreshFixture)
def refreshing_widget(fixture):
    """Clicking on a link, refreshes the displayed text to indicate which link 
       was clicked, without triggering a page load."""

    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.browser

    browser.open('/')

    assert fixture.text_shows_selected(1)    
    assert not fixture.text_shows_selected(3)

    with browser.no_page_load_expected():
        browser.click(XPath.link_with_text('Select 3'))

    assert not fixture.text_shows_selected(1)    
    assert fixture.text_shows_selected(3)    





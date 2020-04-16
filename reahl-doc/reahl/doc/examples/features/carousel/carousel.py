
from reahl.web.fw import UserInterface
from reahl.web.holder.holder import PlaceholderImage
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.grid import Container
from reahl.web.bootstrap.carousel import Carousel


class MyPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.body.use_layout(Container())

        carousel = Carousel(view, 'my_example_carousel_id', show_indicators=True)
        self.body.add_child(carousel)

        carousel.add_slide(PlaceholderImage(view, 900, 500, text='Slide 1', alt='Slide 1 was here'),
                           caption_widget=P(view, text='a paragraph with text'))

        carousel.add_slide(PlaceholderImage(view, 900, 500, text='Slide 2', alt='Slide 2 was here'),
                           caption_widget=P(view, text='a different paragraph'))


class CarouselUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Carousel demo', page=MyPage.factory())




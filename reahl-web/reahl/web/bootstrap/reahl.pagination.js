/* Copyright 2015, 2016, 2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
/*
    This file is part of Reahl.

    Reahl is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation; version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

(function($) {
"use strict";

  $.widget('reahl.bootstrappagemenu', {
      options: {},
      _create: function() {
          var _this = this;
          $(this.element).on('click', 'a', function(event) {
              if ($(event.target).is(_this.allPageLinks())) {
                  _this.changeCurrentPage(_this.pageNumberOf(event.target))
              }
          });
          $(window).on('hashchange', function(e) {
              var newState = e.getState()
              if ('current_page_number' in newState) {
                  _this.changeCurrentPage(newState['current_page_number']);
              }
          });
      },
      allPageLinks: function() {
          return $(this.element).find(">li>a").slice(2, -2)
      },
      allBoundaryLinks: function() {
          var endIndex = $(this.element).find(">li>a").length - 2;
          return $(this.element).find(">li>a")
                                .filter(function(i) {
                                    return i < 2 || i >= endIndex;
                                })
      },
      updateCurrentPageNumber: function(link, number) {
          var href = $(link).attr('href');
          var current_fragment = $.deparam.fragment(href);
          current_fragment['current_page_number'] = number;
          var newHref = $.param.fragment(href, current_fragment, 2);
          $(link).attr('href', newHref);
      },
      changeCurrentPage: function(number) {
          var _this = this;
          _this.allPageLinks().parent().toggleClass('active', false);
          var active_a = _this.linkForPage(number);
          active_a.parent().toggleClass('active', true);
          _this.allBoundaryLinks().filter('[href]').each(function(index, link) {
              _this.updateCurrentPageNumber(link, number)
          });
      },
      pageNumberOf: function(link) {
          var href = $(link).attr('href');
          var current_fragment = $.deparam.fragment(href);
          return current_fragment['current_page_number'];
      },
      linkForPage: function(number) {
	  var _this = this;
          return _this.allPageLinks().filter(function(index) {
              return _this.pageNumberOf(this) == number;
          });
      }
  });

  $.extend($.reahl.bootstrappagemenu, {
      version: '4'
  });

})(jQuery);

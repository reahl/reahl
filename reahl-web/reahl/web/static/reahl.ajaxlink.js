/* Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget('reahl.ajaxlink', {
    options: {
    },

    _create: function() {
        var o = this.options;
        var _this = this;
        this.element.addClass('reahl-ajaxlink');

        var href = this.element.attr('href');
        if (href) {
            var cleanHref = ($.param.querystring(href, {}, 2)).split('?')[0];
            var ajaxHref = href;
            if (href.indexOf('?') >=0) {
                var state = $.deparam.querystring(href);
                ajaxHref = $.param.fragment(cleanHref, state);
                this.element.attr('href', ajaxHref);
            }

            var staysOnPage = ( (!cleanHref) || cleanHref == window.location.pathname);
            if (staysOnPage) {
                var element = this.element;
                this.element.on('click', function() {
                    var current_state = $.deparam.fragment();
                    var current_href = _this.element.attr('href');
                    var newHref = $.param.fragment(current_href, current_state, 1);
                    element.attr('href', newHref);
                    setTimeout(function(){ element.attr('href', current_href);}, 0);
                });
            };
        };
    }
});

$.extend($.reahl.ajaxlink, {
    version: '1.8'
});

})(jQuery);


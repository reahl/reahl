/* Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget("reahl.popupa", {
    // default options
    options: {
        buttons: {},
        showForSelector: 'body'
    },
    _create: function() {
        var o = this.options;
        this.element.addClass("reahl-popupa");

        var $dialog = $("<div></div>");

        var $link = this.element.one("click", function() {
            $dialog
                .load($link.attr("href") + " "+o.showForSelector)
                .modaldialog({
                    title: $link.attr("title"),
                    width: $(window).width()*0.8,
                    height: $(window).height()*0.8,
                    position: 'center',
                    buttons: o.buttons,
                 });

            $link.click(function() {
                $dialog.modaldialog('open');
                return false;
            });

            return false;
        });
    }
});

$.extend($.reahl.popupa, {
    version: "1.8"
});

})(jQuery);



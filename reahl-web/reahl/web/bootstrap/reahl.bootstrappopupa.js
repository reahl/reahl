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

$.widget("reahl.bootstrappopupa", {
    // default options
    options: {
        buttons: {},
        showForSelector: 'body',
        title: '',
    },
    _create: function() {
        var o = this.options;
        var this_ = this;
        this.element.addClass("reahl-bootstrappopupa");

        this_.$dialog = $("<div class='modal fade'> "+
                        "  <div class='modal-dialog' role='document'>"+
                        "    <div class='modal-content'>"+
                        "      <div class='modal-header'>"+
                        "        <h4 class='modal-title'>"+o.title+"</h4>"+
                        "      </div>"+
                        "      <div class='modal-body'>"+
                        "      </div>"+
                        "      <div class='modal-footer'>"+
                        "      </div>"+
                        "    </div>"+
                        "  </div>"+
                        "</div>");
        this_.$footer = this_.$dialog.find(".modal-footer");


        var $link = this.element.one("click", function(e) {
            $( "body" ).append( this_.$dialog ); 
            this_.$dialog.find(".modal-body")
                .load($link.attr("href") + " "+o.showForSelector, function(){
                    $.each(o.buttons, function(label, f) { this_.add_button(label, f) });
                    this_.$dialog.modal({});

                    $link.click(function(e) {
                        this_.$dialog.modal('show');
                        return e.preventDefault();
                    });
                });

            e.preventDefault();
        });
    },
    add_button: function(label, f) {
        var button = $("<button type='button' class='btn' data-dismiss='modal'>"+label+"</button>");
        button.click(f);
        this.$footer.append(button);
    }
});

$.extend($.reahl.bootstrappopupa, {
    version: "1.0"
});

})(jQuery);



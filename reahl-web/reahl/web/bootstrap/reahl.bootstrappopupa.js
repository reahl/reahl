/* Copyright 2016-2020 Reahl Software Services (Pty) Ltd. All rights reserved. */
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
        dismissLabel: '',
        centerVertically: false,
    },
    _create: function() {
        var o = this.options;
        var this_ = this;
        this.element.addClass("reahl-bootstrappopupa");
        var modal_dialog_class = 'modal-dialog';
        if(o.centerVertically){
           modal_dialog_class += ' modal-dialog-centered';
        };

        this_.$dialog = $("<div class='modal fade' data-backdrop='static' tabindex='-1'> "+
                        "  <div class='"+modal_dialog_class+"' role='document'>"+
                        "    <div class='modal-content'>"+
                        "      <div class='modal-header'>"+
                        "        <h4 class='modal-title'>"+o.title+"</h4>"+
                        "        <button type='button' class='close' data-dismiss='modal' aria-label='"+o.dismissLabel+"'><span aria-hidden='true'>&times;</span></button>"+
                        "      </div>"+
                        "      <div class='modal-body'>"+
                        "      </div>"+
                        "      <div class='modal-footer'>"+
                        "      </div>"+
                        "    </div>"+
                        "  </div>"+
                        "</div>");
        this_.$header = this_.$dialog.find(".modal-header");
        this_.$footer = this_.$dialog.find(".modal-footer");


        var $link = this.element.one("click", function(e) {
            $( "body" ).append( this_.$dialog ); 
            this_.$dialog.find(".modal-body")
                .load($link.attr("href") + " "+o.showForSelector, function(){
                    $.each(o.buttons, function(label, opts) { this_.add_button(label, opts) });
                    this_.$dialog.modal({});

                    $link.on('click', function(e) {
                        this_.$dialog.modal('show');
                        return e.preventDefault();
                    });
                });

            e.preventDefault();
        });
    },
    add_button: function(label, opts) {
        var button = $("<button type='button' class='btn' data-dismiss='modal'>"+label+"</button>");
        button.on('click', opts.function);
        for (var i = 0; i < opts.css_classes.length; i+=1) {
            button.addClass(opts.css_classes[i])
        };
        this.$footer.append(button);
    }
});

$.extend($.reahl.bootstrappopupa, {
    version: "1.0"
});

})(jQuery);



/* Copyright 2013, 2014, 2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.blockUI.defaults.css = {};
$.widget("reahl.modaldialog", {
    // default options
    options: {
        coveredElement: 'body',
        position: 'center',
        width: '30%',
        height: '30%',
        left: '35%',
        top: '35%',
        buttons: {}
    },

    _create: function() {
        var o = this.options;
        this.coveredElement = $(o.coveredElement);
        this.element.addClass('reahl-dialogcontent');
        this.dialog = $('<article class="reahl-dialog"></article>');
        this.titleBar = $('<header class="reahl-titlebar"><h1>'+this.options.title+'</h1></header>');
        this.buttons = $('<footer class="reahl-dialogbuttons"></footer>');

        this.dialog.append(this.titleBar);
        this.dialog.append(this.element);
        this.dialog.append(this.buttons);

        this.populateButtons(o.buttons);
        this.computePosition();
        
        this.open();
    },

    computePosition: function() {
        var o = this.options;
        if (o.position == 'center') {
            var offset = this.coveredElement.offset();
            o.left = offset.left+(this.coveredElement.width()-o.width)/2;
            o.top = offset.top+(this.coveredElement.height()-o.height)/2;
        };
    },
    
    populateButtons: function(buttons) {
        var o = this.options;
        for (var name in buttons) {
           var js = buttons[name];
           var button = $('<span class=".reahl-button"><input type="submit" name="'+name+'" value="'+name+'"></span>');
           button.on('click', eval(js));
           button.on('click', function(){
               $(o.coveredElement).unblock();  
               return false;
           });
           this.buttons.append(button);
        };
    },
    
    open: function() {
        var o = this.options;
        this.coveredElement.block({message: this.dialog, 
                                   css: {width: o.width, 
                                         height: o.height, 
                                         left: o.left,
                                         top: o.top}
        });
        this.element.css({overflow: 'auto', 
                          height: o.height-this.buttons.height()-this.titleBar.height()});
    }
});

$.extend($.reahl.modaldialog, {
    version: "1.8"
});

})(jQuery);



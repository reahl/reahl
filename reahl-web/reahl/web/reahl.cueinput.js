/* Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget("reahl.cueinput", {
	_create: function() {
	    var o = this.options;
	    this.element.addClass("reahl-cueinput");

		var input = this.element.find('div input');
		var cue = this.element.find('div.reahl-cue');

        cue.children().each( function() {
             var child = $(this);
             child.attr('hidden', 'true');
        });

        input
            .bind("focus", function(){ 
                cue.children().each( function() {
                    var child = $(this);
                    child.removeAttr('hidden');
                });
            })
            .bind("blur", function(){
                cue.children().each( function() {
                    var child = $(this);
                    child.attr('hidden', 'true');
                });
			});
	}
});

$.extend($.reahl.cueinput, {
	version: "1.8"
});

})(jQuery);



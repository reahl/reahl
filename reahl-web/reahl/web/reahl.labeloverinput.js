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

/* implements plan: http://www.alistapart.com/articles/makingcompactformsmoreaccessible */
(function($) {
"use strict";

$.widget("reahl.labeloverinput", {
	_create: function() {
	    var o = this.options;
	    this.element.addClass("reahl-labeloverinput");
	    this.element.children().filter("label").each( function() {
		    var label = $(this);
		    //		    var input = label.siblings('*[name=' + label.attr("for") +']');
		    var span = label.siblings('span:first');
		    var input = span.find('*[name=' + label.attr("for") +']');
		    label.bind("click", function() {
			    input.focus();
			});
		    input
			.bind("focus", function(){ 
				if ( $(this).val() == "" ) {
    				    label.attr('hidden', 'true');
				}
			    })
			.bind("blur", function(){ 
				if ( $(this).val() == "" ) {
    				    label.removeAttr('hidden');
				}
			    });
		    if ( input.val() == "" ) {
			label.removeAttr('hidden');
		    }
		    else {
			label.attr('hidden', 'true');
		    }
		});
	}
});

$.extend($.reahl.labeloverinput, {
	version: "1.8",
});

})(jQuery);



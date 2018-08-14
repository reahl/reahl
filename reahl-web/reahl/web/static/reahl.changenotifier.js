/* Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
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
    
    $.widget('reahl.changenotifier', {
        options: {
            name: undefined,
        },
        _create: function() {
                var o = this.options;
                var element = this.element;
                var _this = this;
    
                if (!o.name) { throw new Error("No name given in options. This is a required option.")}

                $(element).on( 'change', function(e) {
                    _this.updateHashWithCurrentInputValue(e.target);
                    $(window).hashchange();
                    return true;
                });
        },

        getAllRelatedCheckboxes: function(checkbox, filter) {
            return $('input[name="'+$(checkbox).attr("name")+'"][form="'+$(checkbox).attr("form")+'"]'+filter);
        },

        isCheckboxSelectInputWithMultipleValues: function(checkbox) {
            return !this.isCheckboxInputBoolean(checkbox) && this.getAllRelatedCheckboxes(checkbox, '').length >= 1;
        },

        isCheckboxInputBoolean: function(checkbox) {
            return $(checkbox).attr('type') === 'checkbox' && !$(checkbox).attr('value'); //explicitly use attr instead of .prop
        },

        getAllRelatedCheckedValues: function(checkbox) {
            var checkboxValues = [];
            this.getAllRelatedCheckboxes(checkbox, ':checked').map(function() {
                var checkbox = this;
                checkboxValues.push($(checkbox).val());
            });
            return checkboxValues;
        },

        getCheckboxBooleanValue: function(checkbox) {
           if($(checkbox).is(":checked"))
                return 'on';
           else
                return 'off';
        },

        getCurrentInputValue: function(currentInput) {

            if (this.isCheckboxInputBoolean(currentInput)){
                return this.getCheckboxBooleanValue(currentInput)
            } else
            if (this.isCheckboxSelectInputWithMultipleValues(currentInput)){
                return this.getAllRelatedCheckedValues(currentInput);
            }
            else {
                return currentInput.value;
            }
        },
        
        updateHashWithCurrentInputValue: function(currentInput) {
            var hashName = this.options.name;
            var originalHash = window.location.hash;
            var currentFragment = $.deparam.fragment(originalHash);
            
            currentFragment[hashName] = this.getCurrentInputValue(currentInput);

            var newHash = $.param.fragment(originalHash, currentFragment, 2);
            window.location.hash = newHash;
        }
    });
    
$.extend($.reahl.changenotifier, {
    version: '1.0'
});

})(jQuery);
    
    
    
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

        isCheckbox: function(input) {
            return $(input).attr('type') === 'checkbox';
        },

        isCheckboxForBooleanValue: function(checkbox) {
            return this.isCheckbox(checkbox) && !$(checkbox).is('[value]'); 
        },

        getCheckboxListValue: function(checkbox) {
            var checkboxValues = [];
            var checkedCheckboxes = $('input[name="' + $(checkbox).attr("name") + '"][form="' + $(checkbox).attr("form") + '"]:checked');
            checkedCheckboxes.map(function() {
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
            if (this.isCheckbox(currentInput)) {
                if (this.isCheckboxForBooleanValue(currentInput)){
                    return this.getCheckboxBooleanValue(currentInput)
                } else {
                    return this.getCheckboxListValue(currentInput);
                }
            } else {
                return $(currentInput).val();
            }
        },
        getIsList: function(name) {
            return name.match('\\[\\]$');
        },
        getEmptyListSentinel: function(name) {
            return name+'-';
        },            
        getTraditionallyNamedFragment: function() {
            var untraditionallyNamedFragment = $.deparam.fragment(window.location.hash);
            var traditionallyNamedFragment = {};
            for (var cleanName in untraditionallyNamedFragment) {
                var value = untraditionallyNamedFragment[cleanName];
                var traditionalName;
                if (Array.isArray(value)) {
                    traditionalName = cleanName+'[]';
                } else {
                    traditionalName = cleanName;
                }
                traditionallyNamedFragment[traditionalName] = value;
            }
            return traditionallyNamedFragment;
        },    
        updateHashWithCurrentInputValue: function(currentInput) {
            var _this = this;
            var hashName = this.options.name;
            var currentFragment = _this.getTraditionallyNamedFragment();
            
            var currentInputValue = this.getCurrentInputValue(currentInput);
//            if (Array.isArray(currentInputValue)) {
            if (_this.getIsList(hashName)) {
                var emptySentinelName = _this.getEmptyListSentinel(hashName);
                if ( _.isEqual(currentInputValue,[])) {
                    delete currentFragment[hashName];
                    currentFragment[emptySentinelName] = "";
                } else {
                    delete currentFragment[emptySentinelName];
                    currentFragment[hashName] = currentInputValue;
                }    
            } else {
                currentFragment[hashName] = currentInputValue;
            }

            var newHash = $.param(currentFragment, true);
            window.location.hash = newHash;
        }
    });
    
$.extend($.reahl.changenotifier, {
    version: '1.0'
});

})(jQuery);
    
    
    
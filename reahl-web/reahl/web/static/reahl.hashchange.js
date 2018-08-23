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



$.widget('reahl.hashchange', {
    options: {
            url: '',
            cache: true,
            errorMessage: 'Ajax error',
            timeoutMessage: 'Ajax timeout',
            params: []
    },

    _create: function() {
        var o = this.options;
        var element = this.element;
        var _this = this;

        _this.options.previousHashValues = $.extend(true, {}, _this.options.params);
        $(window).on( 'hashchange', function(e) {
            var currentFragment = _this.getTraditionallyNamedFragment();
            var changedRelevantHashValues = _this.calculateChangedRelevantHashValues(currentFragment);
            if (_this.hasChanged(changedRelevantHashValues)) {
                _this.triggerChange(currentFragment, changedRelevantHashValues);
            };
            return true;
        });
        
        $(window).trigger( 'hashchange' );
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
    getIsList: function(name) {
        return name.match('\\[\\]$');
    },
    getEmptyListSentinel: function(name) {
        return name+'-';
    },
    isEmptyListSentinel: function(name) {
        return name.match('\\[\\]-$');
    },
    getNameFromSentinel: function(name) {
        return name.match('(.*\\[\\])-$')[1];
    },
    getArgumentNames: function() {
        var names = [];
        for (var name in this.options.previousHashValues) {
            if (this.isEmptyListSentinel(name)) {
                name = this.getNameFromSentinel(name);
            }
            names.push(name);
        }
        return names;
    },
    triggerChange: function(currentHashValues, changedHashValues) {
        var _this = this;
        var updatedHashValues = $.extend({}, currentHashValues, changedHashValues);

        var loading = _this.element.block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});
        $.ajax({url:     _this.options.url,
                cache:   _this.options.cache,
                data:    updatedHashValues,
                success: function(data){
                    _this.element.html(data);
                    _this.options.previousHashValues = changedHashValues;
                },
                complete: function(data){
                    _this.element.unblock();
                },
                traditional: true
        });
    },
    hasChanged: function(newHashValues){
        var _this = this;
        var changed = false;
        for (var name in _this.options.previousHashValues) {
            if ( ! _.isEqual(newHashValues[name], _this.options.previousHashValues[name])) {
                changed = true;
            };
            if (_this.getIsList(name)) {
                var emptySentinelName = _this.getEmptyListSentinel(name);
                if (!_.isEqual(newHashValues[emptySentinelName], _this.options.previousHashValues[emptySentinelName])) {
                    changed = true;
                }
            }
        };
        console.log("hasChanged", changed);
        return changed;
    },
    calculateChangedRelevantHashValues: function(currentHashValues) {
        var _this = this;
        var changedRelevantHashValues = {};
        var argumentNames = _this.getArgumentNames();
        for (var i=0; i<argumentNames.length; i++) {
            var name = argumentNames[i];

            var currentValue = currentHashValues[name];
            if (currentValue) {
                changedRelevantHashValues[name]=currentValue;
            } else if (_this.getIsList(name)) {
                var emptySentinelName = _this.getEmptyListSentinel(name);
                if (currentHashValues[emptySentinelName] != undefined) {
                    changedRelevantHashValues[emptySentinelName] = "";
                } else {
                    changedRelevantHashValues[name]=[];
                }
            } else {
                changedRelevantHashValues[name]=_this.options.previousHashValues[name];
            }
        };
        return changedRelevantHashValues;
    },
});

$.extend($.reahl.hashchange, {
    version: '1.8'
});

})(jQuery);



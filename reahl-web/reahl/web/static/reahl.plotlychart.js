/* Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget('reahl.plotlychart', {
    options: { json: {}
    },

    _create: function() {
        var element = this.element;
        element.data('reahlPlotlychart', this);
    },

    update: function(updated_json) {
        Plotly.react(this.element.attr('id'), updated_json);
    }
});

$.extend($.reahl.plotlychart, {
    version: '1.1'
});

$.widget('reahl.plotlychartdata', {
    options: { chart_id: '',
               json: {}
    },

    _create: function() {
        var chart = $('#'+this.options.chart_id).data('reahlPlotlychart');
        chart.update(this.options.json);
    }

});

$.extend($.reahl.plotlychartdata, {
    version: '1.1'
});


})(jQuery);



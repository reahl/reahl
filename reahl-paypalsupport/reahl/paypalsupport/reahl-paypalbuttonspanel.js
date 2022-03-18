/* Copyright 2021, 2022 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

$.widget("reahl.paypalbuttonspanel", {
    options: {
        createOrderUrl: '',
        captureOrderUrl: '',
        returnUrl: '',
        error_announce_text: 'Error while talking to paypal:',
        transaction_not_processed_text: 'Sorry, your transaction could not be processed.'
    },
    _create: function() {
        var o = this.options;
        var this_ = this;
        this.element.addClass("reahl-paypalbuttonspanel");

        paypal.Buttons({
            createOrder: this_.createOrder.bind(this),
            onApprove: this_.onApprove.bind(this)
        }).render('#'+this.element.attr('id'));
    },
    createOrder: function(data, actions) {
        var this_ = this;
        return fetch(this_.options.createOrderUrl, {
            method: 'post',
            redirect: 'error'
        }).then(function(res) {
            if (!(res.status == 200 || res.status == 201)) {
                throw res.statusText;
            }
            return res.json();
        }).then(function(orderData) {
            return orderData.id;
        }).catch(function(reason) {
           var errorUrl = window.location.origin+"/error?error_message="+encodeURIComponent(this_.options.error_announce_text+reason)+"&error_source_href="+encodeURIComponent(window.location.href);
           window.location.href = errorUrl;
        });
    },
    onApprove: function(data, actions) {
        var this_ = this;
        return fetch(this_.options.captureOrderUrl, {
            method: 'post',
            redirect: 'error'
        }).then(function(res) {
            if (res.status != 200) {
                throw res.statusText;
            }
            return res.json();
        }).then(function(orderData) {
            // Three cases to handle:
            //   (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
            //   (2) Other non-recoverable errors -> Show a failure message
            //   (3) Successful transaction -> Show confirmation or thank you

            // This example reads a v2/checkout/orders capture response, propagated from the server
            // You could use a different API or structure for your 'orderData'
            var errorDetail = Array.isArray(orderData.details) && orderData.details[0];

            if (errorDetail && errorDetail.issue === 'INSTRUMENT_DECLINED') {
                return actions.restart(); // Recoverable state, per:
                // https://developer.paypal.com/docs/checkout/integration-features/funding-failure/
            }

            if (errorDetail) {
                var msg = this_.options.transaction_not_processed_text;
                if (errorDetail.description) msg += '\n\n' + errorDetail.description;
                if (orderData.debug_id) msg += ' (' + orderData.debug_id + ')';
                return alert(msg); // Show a failure message (try to avoid alerts in production environments)
            }

            window.location.reload();
        });
    },

});

$.extend($.reahl.paypalbuttonspanel, {
    version: "1.0"
});

})(jQuery);



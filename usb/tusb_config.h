/**
 * Copyright (c) 2023 Raspberry Pi (Trading) Ltd.
 * Modified by Václav Straka in 2025.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#ifndef _TUSB_CONFIG_H_
#define _TUSB_CONFIG_H_

#define CFG_TUD_ENABLED         (1)

//------------------------
// DEVICE CONFIGURATION //
//------------------------

#define CFG_TUSB_RHPORT0_MODE   OPT_MODE_DEVICE

#define CFG_TUD_CDC             (1)
// Set CDC FIFO buffer sizes so Eternity's protocol fits
#define CFG_TUD_CDC_RX_BUFSIZE  (1024)
#define CFG_TUD_CDC_TX_BUFSIZE  (1024)

#define CFG_TUD_CDC_EP_BUFSIZE  (1024)

#define CFG_TUD_ENDPOINT0_SIZE  (64)

#endif /* _TUSB_CONFIG_H_ */

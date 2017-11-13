param = [{

		"num_in":	(2,2),
		"carry_fee":	True,
		"label":	"carry_fee"
	},

#{
#		"ident_out":	(2,1000),
#		"label":	"splitting"
#	},

{
		"num_in":	(5,1000),
		"label":	"many inputs"
	},

{
		"num_in":	(5,1000),
		"num_out":	(5,1000),
		"label":	"possible coinjoin"
	},

{
		"num_in":	(1,2),
		"num_out":	(4,15),
		"label":	"splitting to 4-15 outputs"
	},

{
		"p2sh_out":	(1,1000),
		"label":	"one or more p2sh outputs"
	},

{
		"p2sh_in":	(1,1000),
		"label":	"one or more p2sh inputs"
	},

{
		"num_in":	(1,3),
		"num_out":	(100,100000),
		"label":	"spamminess"
	},

#{
#		"out_range":	(0.000078,0.000078),
#		"label":	"counterparty"
#	},

{
		"p2sh_in":	(1,1),
		"respends":	True,
		"label":	"payment_channel_open"
	},

{
		"respends":	True,
		"label":	"respends"
	}]

Realtime Community Signage
==========================

This code lets set up and run a cheap realtime community sign with a off-the-shelf router and two scrolling LED signs.  All the content for the sign is managed by a centralized server, where you can pick transit or calendar information to display on the signs.

This is part of the Lost In Boston Realtime project of the [MIT Center for Civic Media](http://civic.mit.edu).  This project is about helping people work together to make their neighborhoods more visitor-friendly. Community groups are partnering with local businesses and institutions to install digital signage that call out useful information in their area. 

All the content for the sign is managed by a centralized server, where you can pick transit or calendar information to display on the signs.

Real the INSTALL.md for detailed setup instructions.

Hardware
--------

Right now we run on:

- Netgear WNR3500L Router (you can get these for $60)
- scrolling LED signs from [SignsDirect](http://www.signsdirect.com/) (varying in price)

If you wanted to talk to a different type of LED sign you need to write a new the LedSign python class.

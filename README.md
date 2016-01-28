# Conservamos Deforestation Alerts
We use the Global Forest Watch platform to send out deforestation alerts to private conservation initiatives in Peru.

# How to reuse the code
The code of this project consists of a couple of script we have used to transform shape files and intersect them with alerts provided by GFW, to write alerts to a Google Sheet we use as our main working interface and to obtain raw files from a drive shared in the organisation.
We have tried to comment everything extensively because you will need to change a lot of things in the code to make the system run on your machine or on a server. 
If there's things you don't understand, don't hesitate to create a Github issue or write us an [email](mailto:conservamospornaturaleza@gmail.com)

# Where to find the data
The data product we're using comes from the University of Maryland. They use Landsat images to detect deforestation. It is hosted on the Global Forest Watch platform through the [CartoDB SQL API](https://wri-01.cartodb.com/tables/per_umd_alerts/public/map).
You can head directly to [globalforestwatch.org](http://www.globalforestwatch.org/) to see the dataset visualized. Peruvian concession data is not proper open data yet. You can find shape files of [conservation and ecotourism concessions](https://github.com/Conservamos/deforestation-alerts/tree/master/shapes/con-eco) in this repository. We will try to keep them up to date. Data 

Enjoy!

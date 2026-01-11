## Island Dashboard 
The goal of this assignment is to scope, design, implement and document a data dashboard for an island that addresses the key challenges of said island. The design of the dashboard and its functionality should come from the student; however, you will be introduced to the following tools throughout the course and it is suggested you use one of these: 
- *Gradio*
- *Streamlit*
- *Panel*
- *iPyWidget*
- *Dash* 

Other libraries may be used with instructor permission.

Students should use version control for this assignment, both to demonstrate good practice, to demonstrate authorship and to prevent any loss of code or work. Your application must include the code to make the notebook work in either .py  or .ipynb and all requirements, either in a *requirements.txt* file or *pyproject.toml* file. Assets can be included in the ZIP file – it is also possible to use a bash script command to retrieve these.  

*Please replace this readme file with project documentation.*

## Introduction, Scope and Context (30%) 
You should set the scope of the dashboard, discussing any datasets or databases you will be using (provenance - where they came from, how they came to be collected) and any work needed to get the data in a usable format (cleaning) or to store it before analysis (use of databases, application programming interfaces or data stored in various file formats). You may use any responsibly-sourced data for this project; it is also possible to use synthetic (i.e. fake) data if appropriate, though this may affect the following section. It is worth looking for similar projects in your area, both to provide context and to give you ideas for the analysis and implementation. You should discuss and justify your choice of libraries and tools.
## Methodology and Data Analysis (30%) 
You should talk about and demonstrate your analysis methods and approaches to visualisation here. While the quality of data available will depend on your project, you should be able to demonstrate statistics at the level of collections and subcollections. You should consider what types of visualisations will best convey your insights, and how these will be accessible to your audience. You should also ensure your work is reproducible and that algorithms or formulas used for calculations are documented. 
## Design and Implementation (30%) 
You should show how you constructed the dashboard, demonstrating both the visual and code design. A dashboard implies either interactivity or up-to-date data; ideally, you should include both. This means your dashboard should be interactive and responsive, accommodating different types of users. It should also be updatable, should new data be available. Version control should be used to track the development of new features against documented requirements. You should show knowledge of the classes and methods of libraries used, extending functionality where appropriate. 
## Recommendation, Reflection and Conclusions (10%) 
While this part alone is worth the least number of marks, this is critical for showing the learning that occurred during your work on the assignment, and effective completion of this section will allow you to get more marks in earlier sections. You should link your work to relevant knowledge, skills and behaviour from the apprenticeship, and ensure the marker has everything they need to use and evaluate your code.

---
### Use this section to jot notes of development along with commit messages

As I am using Streamlit, Plotly and the Open-Meteo Weather Forecast API, the documentation/guides I am going to use are going to be noted down below:  
- [StreamLit](https://docs.streamlit.io/develop)  
- [Plotly](https://plotly.com/python/)  
- [Open-Meteo (1)](https://open-meteo.com/en/docs)  
- [Open-Meteo (2)](https://pypi.org/project/openmeteo-requests/)  
- [Open-Meteo (3)](https://github.com/open-meteo/sdk?tab=readme-ov-file#VariablesWithTime)

As the API only allows longitude and latitude inputs, I will use the following github repo to grab cities and their data: https://github.com/lmfmaier/cities-json

According to the research provided in [Exploring Variations in People’s Sources, Uses, and Perceptions of Weather Forecasts](https://journals.ametsoc.org/view/journals/wcas/3/3/2011wcas1061_1.xml), I will pull the following data from the API:
- **NOTE:** Two key factors that came about from their factor analysis was the ‘‘Importance of temperature-related parameters’’ and the ‘‘Importance of precipitation parameters.’’
    - This is paraphased from Pg 181-182, [Exploring Variations in People’s Sources, Uses, and Perceptions of Weather Forecasts](https://journals.ametsoc.org/view/journals/wcas/3/3/2011wcas1061_1.xml)

Factor I1: Importance of temperature-related
forecast parameters

What time of day the high temperature will occur 0.78  
What time of day the low temperature will occur 0.76  
Wind direction 0.62  
How cloudy it will be 0.62  
Humidity levels 0.60  
Low temperature 0.60  
Wind speed 0.59  
High temperature 0.57  


Factor I2: Importance of precipitation
forecast parameters

When precipitation will occur 0.78  
Where precipitation will occur 0.78  
Amount of precipitation 0.71  
Chance of precipitation 0.71  
Type of precipitation 0.71  

Dashboard design should focus on **simplicity**, **relevance**, **consistency** and **interactivity**

According to the review article, _[Design practices in visualization driven data exploration for non-expert audiences](https://www.sciencedirect.com/science/article/pii/S1574013725000085)_, their thematic synthesis process highlights four main engagement methods for dashboard design:
- _Data Driven Storytelling_ - Using the data being presented to create stories that communicate the data better to non-experts, so as to provide a sense of realism to the data
    - Could show how many litres of water the precipitation represents --> more in line with the everyday measurements
    - Using AI to relate the data back to layman
- _Multimodal Interaction_ - Ensuring the system make use of the human's natural way of interacting with the world (e.g touch, sight etc.)
    - Dashboard is inherently interactive
- _Representative Art_ - encompasses a range of artistic implementations and tools such as data comics, animations, virtual environments and infographics
    - Properly space out the visual elements to reduce apparent complexity

- _Hourly_
    - Temperature (2m)      ------> Time-series Line Graph
    - Apparent Temperature
    ---
    - Precipitation Probability ------> Double Axis Bar Chart
    - Precipitation
    ---
    - Wind Speed (10m)  ------> Wind Rose Diagram (sacrifices understanding of dates, worse for detecting trends) --> Use time-series with wind direction listed for each point
    - Wind Direction (10m)
    ---
    - Relative Humidity (2m) ------> Slider + Metrics
    ---
    - Cloud Cover Total     ------> Time-series Line Graph  

- _Daily_
    - Max Temperature (2m)  ------> Max-Min Chart (inspired by Avg-Max-Min chart from Excel)
    - Min Temperature (2m)
    - Max Apparent Temperature (2m)
    - Min Apparent Temperature (2m)
    ---
    - Precipitation Sum ------> Pie Chart
        - Rain Sum
        - Showers Sum       
        - Snowfall Sum
    ---
    - Mean Wind Speed (10m)  ------> Slider + Metrics
    - Dominant Wind Direction (10m)
    ---
    - Mean Precipitation Probability    ------> Time-series Line Graph
    - Mean Cloud Cover
    - Mean Relative Humidity (2m)  

- _Current Weather_
    - **Same as _Hourly_ variables**
        - To focus on the **simplicity** of dashboard design, I will just use _metrics_ with the same groupings as hourly

- Pass this data into Groq AI API using llama-3.3-70b-versatile model to explain what the data shows for the common person and what it affects in the common person's life

- For the general design of my dashboard, I will refer back to the following designs:  
![Dashboard design with a sidebar to filter the graph](misc/Dashboard%20(FULLY%20EXTENDED).png)
![Dashboard design with sidebar collapsed](misc/Dashboard%20(UNEXTENDED).png)


**General research notes I believe will be useful:**
- 'Because ‘‘simply knowing what the weather will be like’’ and ‘‘planning how to dress yourself or your children’’ are the top two forecast uses of those tested in our survey, with 72% and 55% of respondents usually or always using forecasts for them'
    - Pg 181, [Exploring Variations in People’s Sources, Uses, and Perceptions of Weather Forecasts](https://journals.ametsoc.org/view/journals/wcas/3/3/2011wcas1061_1.xml)

- 'Building on findings in LMD09 that, overall, temperature and precipitation were the most important forecast parameters to respondents, these results suggest that _effective_ temperature and precipitation may be most important.'
    - Pg 182, [Exploring Variations in People’s Sources, Uses, and Perceptions of Weather Forecasts](https://journals.ametsoc.org/view/journals/wcas/3/3/2011wcas1061_1.xml)

- 'When designing for information communication, driving a viewer’s or user’s attention and maintaining it is important, and it has been shown that visualizing data when presenting users with an interactive data system, facilitate understanding of said data'
    - Pg 2, [Design practices in visualization driven data exploration for non-expert audiences](https://www.sciencedirect.com/science/article/pii/S1574013725000085)

- 'Our systematic mapping study also revealed that interactivity increases information retention and engagement among non-experts users and allows users to engage in exploration'
    - Pg 13, [Design practices in visualization driven data exploration for non-expert audiences](https://www.sciencedirect.com/science/article/pii/S1574013725000085)

- 'By implementing best practices in information hierarchy, visualization techniques, color psychology, and responsive design, dashboards become powerful decision-support tools that enhance situational awareness and data-driven decision-making.'
    - Pg 7, [The Evolution of Dashboard Design: Best Practices for Data Visualization in Decision Support Systems](https://www.computationalengineeringjournal.com/search?q=ECA-2025-1-004&search=search)


**During write-up, reread the following articles/papers:**
- [Exploring Variations in People’s Sources, Uses, and Perceptions of Weather Forecasts](https://journals.ametsoc.org/view/journals/wcas/3/3/2011wcas1061_1.xml)
- [Design practices in visualization driven data exploration for non-expert audiences](https://www.sciencedirect.com/science/article/pii/S1574013725000085)
- [The Evolution of Dashboard Design: Best Practices for Data Visualization in Decision Support Systems](https://www.computationalengineeringjournal.com/search?q=ECA-2025-1-004&search=search)
To run the project first insatll the required packages listed out in the requirements.txt file
note: It is recommended to create a virtual python environment first using the following command:
python -m venv spam-detection

And then to activate the environment use the following command
source spam-detection/bin/activate

and then proceed with the installation of the packages, you can use the following command:
pip install flask jupyterlab tensorflow twilio python-dotenv pandas seaborn matplotlib wordcloud scikit-learn flask_mysqldb
If the flask_mysqldb package doesn't get install then first run these commands: 
sudo apt-get install libmysqlclient-dev
pip3 install wheel or pip install wheel
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
And then try again
MySQL is also required
Create a database containing a table named "userrs" having the following columns - authid(varchar), id(int, primary key), name(varchar), tno(varchar)
then run the app

If the "jupyter lab" command doesn't work then run the commmand "jupyter notebook"
To retrain the model just run all the cells in the jupyter notebook

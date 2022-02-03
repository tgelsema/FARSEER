"""
Following module contains the flask application that provides 
a user interface to the python implementation of Farseer.

When a user browses to the route for the application, currently "https://farseer.apps.nonprod02.ap.cbsp.nl/",
the index page is loaded, prompting the user for a statistical question.

On input of a question q, farseer.ask(q) gets called returning an answer and explanation.

The user gets redirected to the evaluation page, showing the answer and explanation
and prompting for evaluation of the answer and explanation.

In the case that farseer produces a runtime error, 
the user get redirected to an error page 
kindly requesting to ask another question.

"""
from farseer.ask import ask
from flask import Flask, render_template, redirect, url_for
from flask.globals import request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
import logging
import os
import inspect
import json

from farseer.exec.exc import columntitles

port = 8080

#Create app
app = Flask(__name__)

#Set Logger Level
app.logger.setLevel(logging.INFO)

#Set format for logger
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

#File handler takes care of writing to the right file
filehandler = logging.FileHandler('applog.log')
filehandler.setFormatter(formatter)

#Add logger to app
app.logger.addHandler(filehandler)

# Flask-WTF requires an enryption key - the string can be anything
app.config['SECRET_KEY'] = 'C2HWGVoMGfNTBsrYQg8EcMrdTimkZfAb'

# Flask-Bootstrap requires this line
Bootstrap(app)


class GoBack(FlaskForm):
    """
    Ask user whether he or she wants to go back to homepage
    """
    submit = SubmitField(label='Klik hier om door te gaan')

class QuestionForm(FlaskForm):
    """
    Form asking user to input question
    """
    question = StringField(
                            'Stel hier uw statistische vraag', 
                            validators=[DataRequired()]
                            )
    submit = SubmitField('Versturen')

class EvaluationForm(FlaskForm):
    """
    Form for evaluation of results
    """
    is_answer = SelectField(
                              'Is dit een antwoord op de vraag die u had?', 
                              choices=[('1', 'Ja'), ('2','Nee'), ('3', 'Weet ik niet')], 
                              validators=[DataRequired()]
                              )
    is_clear = SelectField(
                                'Is de toelichting begrijpelijk?', 
                                choices=[('1', 'Ja'), ('2','Nee')], 
                                validators=[DataRequired()]
                             )
    submit = SubmitField('Versturen')

class ApplicationError(Exception):
    """
    General error class for non-html application errors. 
    For debugging, the module of the error is logged as well.
    """
    def __init__(self, question, error):
        frm = inspect.trace()[-1]
        mod = inspect.getmodule(frm[0]) # these lines get module thats source of error
        app.logger.error(f' Question {question} produced error {error}, which occured in module {mod}')

# all Flask routes below

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    'Homepage' prompting user to input their statistical query. 
    On input of 'question', ask(question) gets called returning answer and explanation.
    Then, the user is redirected to
    the ./result page showing the answer and explanation.  
    """
    form = QuestionForm()
    if form.validate_on_submit():
        question = form.question.data
        app.logger.info(f"Question: {question}")
        form.question.data = "" #This is the variable that will be input by the user through the form
        try:
            #On input, this part is triggered
            explanation, answer, columntitles = ask(question)
            expl = {
                            "subjects": explanation[0],
                            "dimensions": explanation[1],
                            "conditions": explanation[2]
                            }
            expl_json = json.dumps(expl)
            rows = [[str(cell) for cell in row] for row in answer]
            rows = [';'.join(row) for row in rows] #turn rows into csv-string for passing to next route
            return redirect(
                            url_for(
                                    'evaluation', 
                                    rows = rows,
                                    columntitles=columntitles, 
                                    explanation=expl_json
                                    )
                            )
        except Exception as e:
            raise ApplicationError(
                                    question=question, 
                                    error=e
                                    )
    return render_template(
                            'index.html', 
                            form=form
                            )

@app.route('/result', methods=['GET', 'POST'])
def evaluation():
    """
    Page showing results and asking user for evaluation.
    """
    eval_form = EvaluationForm()
    rows = request.args.getlist('rows')
    rows = [row.split(';') for row in rows] #parse csv for iterative printing in table
    columntitles = request.args.getlist('columntitles')
    expl_json = request.args.get('explanation')
    expl_dict = json.loads(expl_json)
    #On input, this block in triggered
    if eval_form.validate_on_submit():
        is_answer = eval_form.is_answer.data
        is_clear = eval_form.is_clear.data
        app.logger.info(f"Is Answer?: {is_answer}, Is clear?: {is_clear}")
        return redirect(url_for('thanks_and_ask_again'))
    return render_template('result.html', columntitles=columntitles, rows=rows, expl_dict = expl_dict, eval_form=eval_form)

@app.route('/thanks', methods=["GET", "POST"])
def thanks_and_ask_again():
    form = GoBack()
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('thanks.html', form=form)


# Error handling

@app.errorhandler(ApplicationError)
def application_error(e):
    """
    Page for non-html errors.
    """
    return render_template('oops.html')

@app.errorhandler(404)
def page_not_found(e):
    """
    Page for '404' error.
    """
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """"""
    return render_template('500.html'), 500


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1' # On machines with GPU, loading of all CUDA DLL's takes a long time and we don't need them, so skip.
    app.run(host='0.0.0.0', port=port, debug=True)

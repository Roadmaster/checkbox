#include <QtDBus>
#include <QMessageBox>
#include <QVariantMap>

#include "qtfront.h"
#include "treemodel.h"
#include "step.h"
#include "ui_qtfront.h"

Q_DECLARE_METATYPE(QVariantMap)
//qDBusRegisterMetaType<QVariantMap>();


//qRegisterMetaType<MyType>("MyType");



class CustomQTabWidget : QTabWidget
{
public:
    QTabBar* tabBar(){
        return QTabWidget::tabBar();
    }
};

QtFront::QtFront(QApplication *parent) :
    QDBusAbstractAdaptor(parent),
    ui(new Ui_main),
    m_model(0)
{
    m_mainWindow = new QWidget();
    ui->setupUi(m_mainWindow);
    m_mainWindow->show();

    CustomQTabWidget *tmpQTW = (CustomQTabWidget*)ui->tabWidget;
    tmpQTW->tabBar()->setVisible(false);
    tmpQTW = (CustomQTabWidget*) ui->radioTestTab;
    tmpQTW->tabBar()->setVisible(false);
    ui->radioTestTab->setVisible(false);
    ui->nextPrevButtons->setVisible(false);
    connect(ui->friendlyTestsButton, SIGNAL(clicked()), this, SLOT(onFullTestsClicked()));
//    ui->friendlyTestsButton.clicked.connect(self.onFullTestsClicked)
    connect(ui->buttonStartTesting, SIGNAL(clicked()), this, SLOT(onStartTestsClicked()));
    connect(ui->testTestButton, SIGNAL(clicked()), this, SIGNAL(startTestClicked()));
    connect(ui->yesTestButton, SIGNAL(clicked()), this, SIGNAL(yesTestClicked()));
    connect(ui->noTestButton, SIGNAL(clicked()), this, SIGNAL(noTestClicked()));
    connect(ui->nextTestButton, SIGNAL(clicked()), this, SIGNAL(nextTestClicked()));
    connect(ui->previousTestButton, SIGNAL(clicked()), this, SIGNAL(previousTestClicked()));
    ui->stepsFrame->setFixedHeight(0);
    //skipTestMessage = QErrorMessage()

    titleTestTypes["__audio__"] = "Audio Test";
    titleTestTypes["__bluetooth__"] = "Bluetooth Test";
    titleTestTypes["__camera__"] = "Camera Test";
    titleTestTypes["__cpu__"] = "CPU Test";
    titleTestTypes["__disk__"] = "Disk Test";
    titleTestTypes["__firewire__"] = "Firewire Test";
    titleTestTypes["__graphics__"] = "Graphics Test";
    titleTestTypes["__info__"] = "Info Test";
    titleTestTypes["__input__"] = "Input Test";
    titleTestTypes["__keys__"] = "Keys Test";
    titleTestTypes["__mediacard__"] = "Media Card Test";
    titleTestTypes["__memory__"] = "Memory Test";
    titleTestTypes["__miscellanea__"] = "Miscellanea Test";
    titleTestTypes["__monitor__"] = "Monitor Test";
    titleTestTypes["__networking__"] = "Networking Test";
    titleTestTypes["__wireless__"] = "Wireless Test";
    titleTestTypes["__optical__"] = "Optical Test";
    titleTestTypes["__pcmcia-pcix__"] = "PCMCIA/PCIX Test";
    titleTestTypes["__power-management__"] = "Power Management Test";
    titleTestTypes["__suspend__"] = "Suspend Test";
    titleTestTypes["__usb__"] = "USB Test";
    buttonMap[QMessageBox::Yes] = "yes";
    buttonMap[QMessageBox::No] = "no";

}

void QtFront::onFullTestsClicked()
{
    ui->tabWidget->setCurrentIndex(1);
    emit fullTestsClicked();
}

void QtFront::onStartTestsClicked()
{
    ui->buttonStartTesting->setEnabled(false);
    m_model->setInteraction(false);
    emit startTestsClicked();
}

void QtFront::showText(QString text)
{
    ui->tabWidget->setCurrentIndex(0);
    ui->welcomeTextBox->setPlainText(text);
}

void QtFront::showError(QString text)
{
    QMessageBox::critical(ui->tabWidget, "Error", text);
}

void QtFront::setWindowTitle(QString title)
{
    m_mainWindow->setWindowTitle(title);
}

void QtFront::startProgressBar(QString text)
{
    ui->progressBar->setRange(0, 0);
    ui->progressBar->setVisible(true);
    ui->progressLabel->setVisible(true);
    ui->progressLabel->setText(text);

}

void QtFront::stopProgressBar()
{
    ui->progressBar->setRange(0, 100);
    ui->progressBar->setVisible(false);
    ui->progressLabel->setVisible(false);
    ui->progressLabel->setText("");

}

void QtFront::showTest(QString text, QString testType, bool enableTestButton)
{
    ui->radioTestTab->setVisible(true);
    ui->nextPrevButtons->setVisible(true);
    ui->testTestButton->setEnabled(enableTestButton);
    ui->tabWidget->setCurrentIndex(1);

    foreach(QObject *object, ui->stepsFrame->children())
        object->deleteLater();

    ui->stepsFrame->setFixedHeight(0);
    ui->stepsFrame->update();
    ui->testsTab->setCurrentIndex(2);
    QString purpose = text.split("PURPOSE:\n")[1].split("STEPS:")[0].trimmed();
    QStringList steps = text.split("STEPS:")[1].split("VERIFICATION:")[0].trimmed().split("\n");
    QString verification = text.split("VERIFICATION:")[1].trimmed();

    qDebug() << "purpose" << purpose << "steps"<< steps  <<"verification" << verification;
    QRegExp r("[0-9]+\\. (.*)");
    //r = re.compile(r"[0-9]+\. (.*)")
    int index = 1;
    ui->testTypeLabel->setText(titleTestTypes[testType]);
    ui->purposeLabel->setText(purpose);
    foreach(QString line, steps) {
        bool isInfo = true;
        QString step;
        if (r.indexIn(line.trimmed()) == 0) {
            isInfo = false;
            step = r.cap(1);
        } else {
            step = line;
        }

        Step *a;
        if (isInfo) {
            a = new Step(ui->stepsFrame, step);
        } else {
            a = new Step(ui->stepsFrame, step, QString::number(index));
            index++;
        }

        a->move(0, ui->stepsFrame->height());
        ui->stepsFrame->setFixedHeight(ui->stepsFrame->height() + a->height());
    }
    Step *question = new Step(ui->stepsFrame, verification, QString("?"));
    question->move(0, ui->stepsFrame->height());
    ui->stepsFrame->setFixedHeight(ui->stepsFrame->height() + question->height());

}

void QtFront::showTree(QString text, QMap<QString, QVariant > options)
{
    Q_UNUSED(text);
    ui->testsTab->setCurrentIndex(1);
    ui->radioTestTab->setVisible(false);
    ui->nextPrevButtons->setVisible(false);
    // build the model only once
    if (!this->m_model) {
        this->m_model = new TreeModel();

        QMapIterator<QString, QVariant> i(options);
        while (i.hasNext()) {
            i.next();
            QString section = i.key();
            QStandardItem *sectionItem = new QStandardItem(section);
            sectionItem->setFlags(Qt::ItemIsUserCheckable | Qt::ItemIsEnabled| Qt::ItemIsTristate);
            sectionItem->setData(QVariant(Qt::Checked), Qt::CheckStateRole);
            QDBusArgument arg = i.value().value<QDBusArgument>();
            QMap<QString, QString> items = qdbus_cast<QMap<QString, QString> >(arg);
            QMapIterator<QString, QString> j(items);
            while (j.hasNext()) {
                j.next();
                QString test = j.key();
                if (test.isEmpty())
                    continue;
                QStandardItem *testItem = new QStandardItem(test);
                testItem->setFlags(Qt::ItemIsUserCheckable | Qt::ItemIsEnabled);
                testItem->setData(QVariant(Qt::Checked), Qt::CheckStateRole);
                sectionItem->appendRow(testItem);
            }

            m_model->appendRow(sectionItem);
        }
        ui->treeView->setModel(m_model);
        ui->treeView->show();
    }
    ui->buttonStartTesting->setEnabled(true);
    m_model->setInteraction(true);
}

QString QtFront::showInfo(QString text, QStringList options, QString defaultoption)
{
    int buttons = QMessageBox::NoButton;
    int defaultButton = QMessageBox::NoButton;
    QMessageBox *dialog = new QMessageBox(ui->tabWidget);
    QMap<QAbstractButton*, QString> buttonMap;
    foreach(QString option, options) {
        QAbstractButton *connectButton = dialog->addButton(option, QMessageBox::AcceptRole);
        if (option == defaultoption)
            dialog->setDefaultButton((QPushButton*)connectButton);
        buttonMap[connectButton] = option;
    }
    dialog->setText(text);
    dialog->setWindowTitle("Info");
    int status = dialog->exec();
    QString result = buttonMap[dialog->clickedButton()];
    delete dialog;
    return result;
}


QVariantMap QtFront::getTestsToRun()
{
    QMap<QString, QVariant> selectedOptions;

    int numRows = m_model->rowCount();
    for(int i=0; i< numRows; i++) {
        QStandardItem *item = m_model->item(i, 0);
        QMap<QString, QVariant> itemDict;
        for(int j=0; j< item->rowCount(); j++) {
            if (item->child(j)->checkState() == Qt::Checked || item->child(j)->checkState() == Qt::PartiallyChecked) {
                itemDict[item->child(j)->text()] = QString("");
            }
        }

        if (item->checkState() == Qt::Checked || item->checkState() == Qt::PartiallyChecked) {
            selectedOptions[item->text()] = QVariant::fromValue<QVariantMap>(itemDict);
        }
    }

    return selectedOptions;
}

QtFront::~QtFront()
{
    delete ui;
}

bool QtFront::registerService() {
    QDBusConnection connection = QDBusConnection::sessionBus();
    if ( !connection.registerService("com.canonical.QtCheckbox") ) {
         qDebug() << "error registering service.";
         return false;
     }
     if ( !connection.registerObject("/QtFront", this) ) {
         qDebug() << "error registering object";
         return false;
     }

     return true;
}

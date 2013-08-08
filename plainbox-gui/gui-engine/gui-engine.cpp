/*
 * This file is part of plainbox-gui
 *
 * Copyright 2013 Canonical Ltd.
 *
 * Authors:
 * - Andrew Haigh <andrew.haigh@cellsoftware.co.uk>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "gui-engine.h"
#include <QtDBus/QtDBus>
#include <QDebug>

#include "PBTreeNode.h"

// Forward declarations
void decodeDBusArgType(const QDBusArgument &arg);       // temporary
void decodeDBusMessageType(const QDBusMessage &msg);    // temporary

void GuiEnginePlugin::registerTypes(const char *uri)
{
    // register our classes
    qmlRegisterType<GuiEngine>(uri,1,0,"GuiEngine");
}

GuiEngine::GuiEngine( QObject*parent ) :
    QObject(parent),
    enginestate(UNINITIALISED),
    pb_objects(NULL),
    valid_pb_objects(false),
    job_tree(NULL),
    m_local_jobs_done(false)

{
    qDebug("GuiEngine::GuiEngine");

    // Nothing to do here

    qDebug("GuiEngine::GuiEngine - Done");
}

bool GuiEngine::Initialise(void)
{
    qDebug("GuiEngine::Initialise");

    // Only do this once
    if (enginestate==UNINITIALISED) {

        qDebug("GuiEngine - Initialising");

        // Connect to Dbus Session Bus
        if (!QDBusConnection::sessionBus().isConnected()) {
            qDebug("Cannot connect to the D-Bus session bus.\n");

            return false;
        }

        // Register our custom types for unpacking the object tree
        qDBusRegisterMetaType<om_smalldict>();
        qDBusRegisterMetaType<om_innerdict>();
        qDBusRegisterMetaType<om_outerdict>();

        // We need to pack ObjectPaths into an array for CreateSession()
        qDBusRegisterMetaType<opath_array_t>();

        // Obtain the initial tree of Plainbox objects, starting at the root "/"
        pb_objects = new PBTreeNode();
        pb_objects->AddNode(pb_objects, QDBusObjectPath("/"));
        if (!pb_objects) {
            qDebug("Failed to get Plainbox Objects");

            return false;
        }

        // Connect our change receivers
        QDBusConnection bus = QDBusConnection ::sessionBus();

// FIXME - We will want these for process real job signals. For now they clutter the log :)
//        if (!bus.connect(PBBusName, \
//                         PBObjectPathName, \
//                         ofDObjectManagerName,\
//                         "InterfacesAdded",\
//                         this,\
//                         SLOT(InterfacesAdded(QDBusMessage)))) {

//            qDebug("Failed to connect slot for InterfacesAdded events");

//            return false;
//        }

//        if (!bus.connect(PBBusName,\
//                         PBObjectPathName,\
//                         ofDObjectManagerName,\
//                         "InterfacesRemoved",\
//                         this,\
//                         SLOT(InterfacesRemoved(QDBusMessage)))) {

//            qDebug("Failed to connect slot for InterfacesRemoved events");

//            return false;
//        }

        // Connect the JobResultAvailable signal receiver
        if (!bus.connect(PBBusName,\
                         NULL,\
                         PBInterfaceName,\
                         "JobResultAvailable",\
                         this,\
                         SLOT(JobResultAvailable(QDBusMessage)))) {

            qDebug("Failed to connect slot for JobResultAvailable events");

            return false;
        }

        enginestate = READY;
    }

    qDebug("GuiEngine::Initialise() - Done");

    return true;
}

bool GuiEngine::Shutdown(void)
{
    qDebug("GuiEngine::Shutdown()");

    // Were we initialised?
    if (enginestate==UNINITIALISED) {
        qDebug("Plainbox GUI Engine not initialised");
        return false;
    }

    QDBusInterface iface(PBBusName, \
                         PBObjectPathName, \
                         PBInterfaceName, \
                         QDBusConnection::sessionBus());
    if (!iface.isValid()) {
        qDebug("Cant get Plainbox Service interface");
        return false;
    }

    QDBusMessage reply = iface.call("Exit");
    if (reply.type() != QDBusMessage::ReplyMessage) {

        qDebug() << "Failed to exit Plainbox" << reply.errorMessage();

        return false;
    }

    enginestate=UNINITIALISED;

    qDebug("GuiEngine::Shutdown() - Done");

    return true;
}

// DBus-QT Demarshalling helper functions
const QDBusArgument &operator>>(const QDBusArgument &argument, \
                                om_smalldict &smalldict)
{
    argument.beginMap();
    smalldict.clear();

    while(!argument.atEnd())
    {
        argument.beginMapEntry();

        QString property;
        QDBusVariant variant;

        argument >> property >> variant;

        qDebug() << "string" \
                 << property \
                 << "variant: " \
                 << variant.variant().toString();

        smalldict.insert(property,variant);

        argument.endMapEntry();
    }

    argument.endMap();

    return argument;
}

const QDBusArgument &operator>>(const QDBusArgument &argument, \
                                om_innerdict &innerdict)
{
    argument.beginMap();
    innerdict.clear();

    while(!argument.atEnd())
    {
        argument.beginMapEntry();

        QString interface;
        om_smalldict sd;

        argument >> interface >> sd;

        qDebug() << "Interface: " << interface;

        innerdict.insert(interface,sd);

        argument.endMapEntry();
    }

    argument.endMap();

    return argument;
}

const QDBusArgument &operator>>(const QDBusArgument &argument, \
                                om_outerdict &outerdict)
{
    argument.beginMap();
    outerdict.clear();

    while(!argument.atEnd())
    {
        argument.beginMapEntry();

        QDBusObjectPath object_path;
        om_innerdict innerdict;

        argument >> object_path >> innerdict;

        qDebug() << "ObjectPath" \
                 << object_path.path();

        argument.endMapEntry();

        outerdict.insert(object_path,innerdict);
    }

    argument.endMap();

    return argument;
}

const PBTreeNode* GuiEngine::GetRootJobsNode(const PBTreeNode* node)
{
    // Are we there yet
    if (node->object_path.path() == "/plainbox/job") {
        return node;
    }

    PBTreeNode* jobnode = NULL;

    QList<PBTreeNode*>::const_iterator iter= node->children.begin();

    while(!jobnode && iter !=  node->children.end()) {

        PBTreeNode* child = *iter;

        jobnode = const_cast<PBTreeNode*>(GetRootJobsNode(child));
        if (jobnode) {
            return jobnode;
        }

        iter++;
    }

    return NULL;
}

const PBTreeNode* GuiEngine::GetRootWhiteListNode(const PBTreeNode* node)
{
    // Are we there yet
    if (node->object_path.path() == "/plainbox/whitelist") {
        return node;
    }

    PBTreeNode* whitenode = NULL;

    QList<PBTreeNode*>::const_iterator iter= node->children.begin();

    while(!whitenode && iter !=  node->children.end()) {

        PBTreeNode* child = *iter;

        whitenode = const_cast<PBTreeNode*>(GetRootWhiteListNode(child));
        if (whitenode) {
            return whitenode;
        }

        iter++;
    }

    return NULL;
}

// Work in progress
void GuiEngine::InterfacesAdded(QDBusMessage msg)
{
    qDebug("GuiEngine::InterfacesAdded");

    QList<QVariant> args = msg.arguments();

    QList<QVariant>::iterator p = args.begin();

    p = args.begin();

    QVariant q = *p;

    QDBusObjectPath opath = q.value<QDBusObjectPath>();

    qDebug() << "objectpath: " << opath.path();

    p++;

    q = *p;

    const QDBusArgument qda = q.value<QDBusArgument>();

    om_innerdict my_id;

    qda >> my_id;

    // Need to update our tree of objects.

    // todo

    // Now tell the GUI to update its knowledge of the objects
    emit UpdateGuiObjects();

    qDebug("GuiEngine::InterfacesAdded - done");
}

// Work in progress
void GuiEngine::InterfacesRemoved(QDBusMessage msg)
{
    qDebug("GuiEngine::InterfacesRemoved");

    // Need to update our tree of objects.

    qDebug() << "Signature is: " << msg.signature();

    QList<QVariant> args = msg.arguments();

    qDebug("Reply arguments: %d",args.count());

    QList<QVariant>::iterator p = args.begin();

    p = args.begin();

    QVariant q = *p;

    QDBusObjectPath opath = q.value<QDBusObjectPath>();

    qDebug() << "opath: " << opath.path();

    p++;

    q = *p;

    const QDBusArgument qda = q.value<QDBusArgument>();

    // Need to update our tree of objects.

    // todo

    // Now tell the GUI to update its knowledge of the objects
    emit UpdateGuiObjects();

    qDebug("GuiEngine::InterfacesRemoved - done");
}

QList<PBTreeNode*> GuiEngine::GetJobNodes(void)
{
    //qDebug("GuiEngine::GetJobNodes()");

    QList<PBTreeNode*> jobnodes;

    PBTreeNode* jobnode = \
            const_cast<PBTreeNode*>(GetRootJobsNode(pb_objects));
    if (!jobnode) {
        return jobnodes;
    }

    QList<PBTreeNode*>::const_iterator iter =jobnode->children.begin();

    while(iter != jobnode->children.end()) {

        PBTreeNode* child = *iter;

         jobnodes.append(child);

         iter++;
    }

    //qDebug("GuiEngine::GetJobNodes() - done");

    return jobnodes;
}

QList<PBTreeNode*> GuiEngine::GetWhiteListNodes(void)
{
    qDebug("GuiEngine::GetWhiteListNodes()");

    QList<PBTreeNode*> whitelistnodes;

    PBTreeNode* whitelistnode = \
            const_cast<PBTreeNode*>(GetRootWhiteListNode(pb_objects));
    if (!whitelistnode) {
        return whitelistnodes;
    }

    QList<PBTreeNode*>::const_iterator iter = whitelistnode->children.begin();

    while(iter != whitelistnode->children.end()) {

        PBTreeNode* child = *iter;

         whitelistnodes.append(child);

         iter++;
    }

    qDebug("GuiEngine::GetWhiteListNodes() - done");

    return whitelistnodes;
}

QMap<QDBusObjectPath,QString> GuiEngine::GetWhiteListPathsAndNames(void)
{
    QMap<QDBusObjectPath,QString> paths_and_names;

    PBTreeNode* whitenode = \
            const_cast<PBTreeNode*>(GetRootWhiteListNode(pb_objects));
    if (!whitenode) {
        return paths_and_names;
    }

    // loop around all the children
    QList<PBTreeNode*>::const_iterator iter =whitenode->children.begin();

    bool initialised = ! whitelist.empty();

    while(iter != whitenode->children.end()) {

        PBTreeNode* child = *iter;

        QString opath = child->object_path.path();

        // Connect to the introspectable interface
        QDBusInterface introspect_iface(PBBusName, \
                             opath, \
                             "org.freedesktop.DBus.Properties", \
                             QDBusConnection::sessionBus());

        if (introspect_iface.isValid()) {
            QDBusReply<QVariant> reply  = introspect_iface.call("Get", \
                       "com.canonical.certification.PlainBox.WhiteList1", \
                       "name");

            QVariant var(reply);

            QString name(var.toString());

            qDebug() << name;

            paths_and_names.insert(child->object_path,name);

            // First time round, fill in our whitelist member
            if (!initialised) {
                whitelist.insert(child->object_path,true);
            }
        }

        iter++;
    }

    return paths_and_names;
}

void GuiEngine::SetWhiteList(const QDBusObjectPath opath, const bool check)
{
    whitelist.remove(opath);

    whitelist.insert(opath,check);
}

// temporary helper
void GuiEngine::dump_whitelist_selection(void)
{
    // loop around all the children
    QMap<QDBusObjectPath,bool>::const_iterator iter = whitelist.begin();

    while(iter != whitelist.end() ) {

        bool yes = iter.value();

        qDebug() << iter.key().path() << (yes ? "Yes" : "No");

        iter++;
    }
}

/* Run all the local "generator" jobs selected by the whitelists, in order
 * to generate the correct "via" information for the _real_ jobs
 * which the user may want to run. This gives us our hierarchy to
 * show in the test selection screen.
 *
 * For clarity of understanding, the flow/style follows dbus-mini-client.py
 */
void GuiEngine::RunLocalJobs(void)
{
    qDebug("GuiEngine::RunLocalJobs");

    /* Whitelist is selected elsewhere in GetWhiteListPathsAndNames()
     * so by this point its contained in the member variable "whitelist"
     * mini-runner gets these via GetManagedObjects. but it appears to be
     * the same list as exposed by actually trawling DBus itself.
     */

    // Create a session and "seed" it with my job list:
    m_job_list = GetAllJobs();

    // Create a session
    m_session = CreateSession(m_job_list);

    // to get only the *jobs* that are designated by the whitelist.
    m_desired_job_list = GenerateDesiredJobList(m_job_list);

    // This is just the list of all provider jobs marked "local"
    m_local_job_list = GetLocalJobs();

    // desired local jobs are the Union of all local jobs and the desired jobs
    m_desired_local_job_list = JobTreeNode::FilteredJobs(m_local_job_list,m_desired_job_list);

    // Now I update the desired job list.
    QStringList errors = UpdateDesiredJobList(m_session, m_desired_local_job_list);
    if (errors.count() != 0) {
        qDebug("UpdateDesiredJobList generated errors:");

        for (int i=0; i<errors.count(); i++) {
            qDebug() << errors.at(i);
        }
    }

    // Now, the run_list contains the list of jobs I actually need to run \o/
    m_run_list = SessionStateRunList(m_session);
    qDebug() << "Running Local Job " << JobNameFromObjectPath(m_run_list.first());

    RunJob(m_session,m_run_list.first());

    qDebug("GuiEngine::RunLocalJobs - Done");
}

bool GuiEngine::WhiteListDesignates(const QDBusObjectPath white_opath, \
                                    const QDBusObjectPath job_opath)
{
    /*
      qDebug() << "GuiEngine::WhiteListDesignates " << white_opath.path() << \
                job_opath.path();
    */

    QDBusInterface iface(PBBusName, \
                         white_opath.path(), \
                         PBWhiteListInterface, \
                         QDBusConnection::sessionBus());
    if (!iface.isValid()) {
        qDebug("Could not connect to \
               com.canonical.certification.PlainBox.WhiteList1 interface");
    }

    QDBusReply<bool> reply = \
            iface.call("Designates",\
                       QVariant::fromValue<QDBusObjectPath>(job_opath));
    if (!reply.isValid()) {

        qDebug() << "Failed to call whitelist Designates" << \
                    reply.error().name();

        return false;   // Error case defaults to dont run
    }

    return reply.value();
}

QDBusObjectPath GuiEngine::CreateSession(QList<QDBusObjectPath> job_list)
{
    QDBusObjectPath session;

    QDBusInterface iface(PBBusName, \
                         PBObjectPathName, \
                         PBInterfaceName, \
                         QDBusConnection::sessionBus());
    if (!iface.isValid()) {
        qDebug("Could not connect to \
               com.canonical.certification.PlainBox.Service1 interface");
        return session;
    }

    QDBusReply<QDBusObjectPath> reply = \
            iface.call("CreateSession",\
                       QVariant::fromValue<opath_array_t>(job_list));
    if (reply.isValid()) {
        session = reply.value();
    } else {
        qDebug("Failed to CreateSession()");
    }

    return session;
}

QList<QDBusObjectPath> GuiEngine::GetLocalJobs(void)
{
    QList<QDBusObjectPath> generator_jobs;

    QList<PBTreeNode*> jobnodes = GetJobNodes();

    QList<PBTreeNode*>::const_iterator iter = jobnodes.begin();

    while(iter != jobnodes.end()) {

        PBTreeNode* node = *iter;

        QList<PBObjectInterface*> interfaces = node->interfaces;

        // Now find the plainbox interface
        for (int i=0; i< interfaces.count(); i++) {
            if (interfaces.at(i)->interface.compare(CheckBoxJobDefinition1) == 0) {

                // Now we need to find the plugin property
                QVariant variant;

                variant = interfaces.at(i)->properties.find("plugin").value();

                if (variant.isValid() && variant.canConvert(QMetaType::QString)) {
                    if (variant.toString().compare("local") == 0) {

                        // now append this to the list of jobs for CreateSession()
                        generator_jobs.append(node->object_path);
                    }
                }
            }
        }

        iter++;
    }

    return generator_jobs;
}

QList<QDBusObjectPath> GuiEngine::GetAllJobs(void)
{
    QList<QDBusObjectPath> jobs;

    QList<PBTreeNode*> jobnodes = GetJobNodes();

    QList<PBTreeNode*>::const_iterator iter = jobnodes.begin();

    while(iter != jobnodes.end()) {

        PBTreeNode* node = *iter;

        // now append this to the list of jobs to feed to CreateSession()
        jobs.append(node->object_path);

        iter++;
    }

    return jobs;
}


/* Shouldnt this really return QList<QDBusObjectPath> ?
 *
 * At present it doesnt because it matches the Plainbox return type, which
 * appears to be inconsistent at least.
 */
QStringList GuiEngine::UpdateDesiredJobList(const QDBusObjectPath session, \
                                            QList<QDBusObjectPath> desired_job_list)
{
    QStringList job_list;

    QDBusInterface iface(PBBusName, \
                         session.path(), \
                         PBSessionStateInterface, \
                         QDBusConnection::sessionBus());
    if (!iface.isValid()) {
        qDebug("Could not connect to \
               com.canonical.certification.PlainBox.Service1 interface");
        return job_list;
    }

    QDBusReply<QStringList> reply = \
            iface.call("UpdateDesiredJobList",\
                       QVariant::fromValue<opath_array_t>(desired_job_list));
    if (reply.isValid()) {
        job_list = reply.value();
    } else {
        qDebug("Failed to CreateSession()");
    }

    return job_list;
}

QList<QDBusObjectPath> GuiEngine::SessionStateRunList(const QDBusObjectPath session)
{
    PBTreeNode node;

    QVariantMap map = node.GetObjectProperties(session,PBSessionStateInterface);

    QList<QDBusObjectPath> opathlist;

    QVariantMap::iterator iter = map.find("run_list");

    QVariant variant = iter.value();

    const QDBusArgument qda = variant.value<QDBusArgument>();

    qda >> opathlist;

    return opathlist;
}

QList<QDBusObjectPath> GuiEngine::SessionStateJobList(const QDBusObjectPath session)
{
    PBTreeNode node;

    QVariantMap map = node.GetObjectProperties(session,PBSessionStateInterface);

    QList<QDBusObjectPath> opathlist;

    QVariantMap::iterator iter = map.find("job_list");

    QVariant variant = iter.value();

    const QDBusArgument qda = variant.value<QDBusArgument>();

    qda >> opathlist;

    return opathlist;
}


void GuiEngine::RunJob(const QDBusObjectPath session, \
                       const QDBusObjectPath opath)
{
//    qDebug() << "RunJob() " << session.path() << " " << opath.path();

    QStringList job_list;

    QDBusInterface iface(PBBusName, \
                         PBObjectPathName, \
                         PBInterfaceName, \
                         QDBusConnection::sessionBus());
    if (!iface.isValid()) {
        qDebug() <<"Could not connect to " << PBInterfaceName;

        return;
    }

    QDBusPendingCall async_reply = iface.asyncCall("RunJob", \
                QVariant::fromValue<QDBusObjectPath>(session), \
                QVariant::fromValue<QDBusObjectPath>(opath));

    QDBusPendingCallWatcher watcher(async_reply,this);

    watcher.waitForFinished();

    QDBusPendingReply<QString,QByteArray> reply = async_reply;
    if (reply.isError()) {

        // For the moment, we wont get the "say" signature, just "o"
        QDBusError qde = reply.error();

        if (qde.name().compare("org.freedesktop.DBus.Error.InvalidSignature") !=0) {
            qDebug() << qde.name() << " " << qde.message();
        }
    }
}

// temporary - Print the DBus argument type
void decodeDBusArgType(const QDBusArgument &arg)
{
    // Print the signature
    qDebug() << "Signature is: "<< arg.currentSignature();

    QString type;

    switch (arg.currentType())
    {
    case QDBusArgument::BasicType:
        type = "BasicType";
        break;

    case QDBusArgument::VariantType:
        type = "VariantType";
        break;

    case QDBusArgument::ArrayType:
        type = "ArrayType";
        break;

    case QDBusArgument::StructureType:
        type = "StructureType";
        break;

    case QDBusArgument::MapType:
        type = "MapType";
        break;

    case QDBusArgument::MapEntryType:
        type = "MapEntryType";
        break;

    case QDBusArgument::UnknownType:
        type = "Unknown";
        break;

    default:
        type = "UNRECOGNISED";
    }

    qDebug() << "Type: " << type;
}

// temporary - print the DBus message reply type
void decodeDBusMessageType(const QDBusMessage &msg)
{
    QString type;

    switch (msg.type())
    {
        case QDBusMessage::MethodCallMessage:
        type = "MethodCallMessage";
        break;

        case QDBusMessage::SignalMessage:
        type = "SignalMessage";
        break;

        case QDBusMessage::ReplyMessage:
        type = "ReplyMessage";
        break;

        case QDBusMessage::ErrorMessage:
        type = "ErrorMessage";
        break;

        case QDBusMessage::InvalidMessage:
        type = "InvalidMessage";
        break;

        default:
        type = "UNRECOGNISED";
    }

    qDebug() << "Type: " << type << msg.errorMessage() << " " << msg.errorName();
}

JobTreeNode* GuiEngine::GetJobTreeNodes(void)
{
    if (job_tree) {
        // lets re-build it as the PBTree may have changed
        delete job_tree;
    }

    job_tree = new JobTreeNode();

    // Get our list of jobs
    QList<PBTreeNode*> jobnodes = GetJobNodes();

    for (int i = 0; i< jobnodes.count(); i++) {
        /* We assemble a path of PBTreeNodes to represent the chain to the
        * top of our notional tree. It will be in discovered order.
        */
        PBTreeNode* node = jobnodes.at(i);

        QList<PBTreeNode*> chain;

        PBTreeNode* next = node;

        while(next) {
            chain.prepend(next);

            next = PBTreeNode::FindJobNode(next->via(),jobnodes);
        }

        job_tree->AddNode(job_tree, chain);
    }

    return job_tree;
}


QList<QDBusObjectPath> GuiEngine::GenerateDesiredJobList(QList<QDBusObjectPath> job_list)
{
    QList<QDBusObjectPath> desired_job_list;

    // Iterate through each whitelist, and check if it Designates each job
    QMap<QDBusObjectPath, bool>::iterator iter = whitelist.begin();
    while(iter != whitelist.end()) {

        // Try it if we have selected this whitelist
        if (iter.value()) {
            QDBusObjectPath white = iter.key();

            // local_jobs
            for(int i=0; i < job_list.count(); i++) {

                QDBusObjectPath job = job_list.at(i);

                // Does the whitelist designate this job?
                bool ok = WhiteListDesignates(white,job);

                // If ANY whitelist wants this job, we say yes
                if (ok) {
                    if (!desired_job_list.contains(job)) {
                        desired_job_list.append(job);
                    }
                }
            }
        }

        // Next whitelist
        iter++;
    }

    return desired_job_list;
}

void GuiEngine::UpdateJobResult(const QDBusObjectPath session, \
                                           const QDBusObjectPath &job_path, \
                                           const QDBusObjectPath &result_path
                                           )
{
//    qDebug() << "UpdateJobResult() " << session.path() << " " << job_path.path();

    QDBusInterface iface(PBBusName, \
                         session.path(), \
                         PBSessionStateInterface, \
                         QDBusConnection::sessionBus());
    if (!iface.isValid()) {
        qDebug() <<"Could not connect to " << PBInterfaceName;

        return;
    }

    QDBusMessage reply = \
            iface.call("UpdateJobResult", \
                       QVariant::fromValue<QDBusObjectPath>(job_path), \
                       QVariant::fromValue<QDBusObjectPath>(result_path));

    if (reply.type() != QDBusMessage::ReplyMessage) {
        qDebug() << "Error: " << reply.errorName() << " " << reply.errorName();
    }
}

void GuiEngine::JobResultAvailable(QDBusMessage msg)
{
//    qDebug("GuiEngine::JobResultAvailable");

    /* We need information about which job and jobresult we should look at
     * in order to call UpdateJobResult().
     */

    QList<QVariant> args = msg.arguments();

    QList<QVariant>::iterator iter = args.begin();

    QVariant variant = *iter;

    QDBusObjectPath job = variant.value<QDBusObjectPath>();

    iter++;

    variant = *iter;

    QDBusObjectPath result = variant.value<QDBusObjectPath>();

    UpdateJobResult(m_session,job,result);

    // Pull the first thing off the list and discard it
    m_run_list.pop_front();

    if (!m_run_list.empty()) {
        // Now run the next job
        qDebug() << "Running Local Job " << JobNameFromObjectPath(m_run_list.first());

        RunJob(m_session,m_run_list.first());

        return;
    }

    qDebug("All Local Jobs completed\n");

    // Now I update the desired job list to get jobs created from local jobs.
    QStringList errors = UpdateDesiredJobList(m_session, m_desired_job_list);
    if (errors.count() != 0) {
        qDebug("UpdateDesiredJobList generated errors:");

        for (int i=0; i<errors.count(); i++) {
            qDebug() << errors.at(i);
        }
    }

    // get the job-list: NB: From the SessionState this time
    m_job_list = SessionStateJobList(m_session);

    // to get only the *jobs* that are designated by the whitelist.
    m_desired_job_list = GenerateDesiredJobList(m_job_list);

    /* Now I update the desired job list.
        XXX: Remove previous local jobs from this list to avoid evaluating
        them twice
    */
    errors = UpdateDesiredJobList(m_session, m_desired_job_list);
    if (errors.count() != 0) {
        qDebug("UpdateDesiredJobList generated errors:");

        for (int i=0; i<errors.count(); i++) {
            qDebug() << errors.at(i);
        }
    }

    // Now, the run_list contains the list of jobs I actually need to run \o/
    m_run_list = SessionStateRunList(m_session);

    // Now, store the list of valid runnable jobs for the GUI
    valid_run_list = m_run_list;

    // We must have reached the end, so
    if (pb_objects) {
        delete pb_objects;
    }

    // Obtain the initial tree of Plainbox objects, starting at the root "/"
    pb_objects = new PBTreeNode();
    pb_objects->AddNode(pb_objects, QDBusObjectPath("/"));
    if (!pb_objects) {
        qDebug("Failed to get Plainbox Objects");
    }

    // we should emit a signal to say its all done
    emit localJobsCompleted();

    // qDebug("GuiEngine::JobResultAvailable - Done");

}

void GuiEngine::AcknowledgeJobsDone(void)
{
    qDebug("GuiEngine::AcknowledgeJobsDone()");

    m_local_jobs_done = true;

    qDebug("GuiEngine::AcknowledgeJobsDone() - done");
}

const QString GuiEngine::JobNameFromObjectPath(const QDBusObjectPath& opath)
{
    QString empty;

    QList<PBTreeNode*> jlist = GetJobNodes();

    for(int i=0;i<jlist.count();i++) {
        if (jlist.at(i)->object_path.path().compare(opath.path()) == 0) {
            return jlist.at(i)->name();
        }
    }

    return empty;
}
